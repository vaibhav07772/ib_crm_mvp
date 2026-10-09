"""
IB Networking CRM - Free Student MVP
Streamlit Dashboard
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database.db import get_session, Contact, EmailLog, Suppression, init_db
from services.llm_drafter import LLMDrafter
from services.email_finder import EmailFinder
from services.email_sender import EmailSender
from config.settings import STUDENT_NAME, DAILY_EMAIL_LIMIT

st.set_page_config(
    page_title="IB Networking CRM",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# -------------------- Helpers --------------------
def load_contacts(status_filter=None):
    session = get_session()
    query = session.query(Contact)
    if status_filter and status_filter != "All":
        query = query.filter(Contact.status == status_filter)
    contacts = query.order_by(Contact.created_at.desc()).all()
    session.close()
    return contacts


def get_stats():
    session = get_session()
    total = session.query(Contact).count()
    new = session.query(Contact).filter(Contact.status == "new").count()
    drafted = session.query(Contact).filter(Contact.status == "drafted").count()
    approved = session.query(Contact).filter(Contact.status == "approved").count()
    sent = session.query(Contact).filter(Contact.status == "sent").count()
    replied = session.query(Contact).filter(Contact.status == "replied").count()
    session.close()
    return {
        "total": total,
        "new": new,
        "drafted": drafted,
        "approved": approved,
        "sent": sent,
        "replied": replied,
    }


# -------------------- Sidebar --------------------
st.sidebar.title("IB Networking CRM")
st.sidebar.caption(f"Student: {STUDENT_NAME}")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Contacts", "Add Contact", "Draft & Approve", "Send Emails", "Import CSV", "Settings"],
)

# -------------------- Dashboard --------------------
if page == "Dashboard":
    st.title("📊 Dashboard")
    stats = get_stats()

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Contacts", stats["total"])
    col2.metric("New", stats["new"])
    col3.metric("Drafted", stats["drafted"])
    col4.metric("Approved", stats["approved"])
    col5.metric("Sent", stats["sent"])
    col6.metric("Replied", stats["replied"])

    st.markdown("---")
    st.subheader("Recent Contacts")
    contacts = load_contacts()[:20]
    if contacts:
        df = pd.DataFrame([
            {
                "Name": f"{c.first_name or ''} {c.last_name or ''}".strip(),
                "Email": c.email,
                "Title": c.title,
                "Company": c.company,
                "Status": c.status,
                "Source": c.source,
            }
            for c in contacts
        ])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No contacts yet. Add some from the sidebar.")

# -------------------- Contacts --------------------
elif page == "Contacts":
    st.title("👥 All Contacts")
    status = st.selectbox("Filter by Status", ["All", "new", "drafted", "approved", "sent", "replied", "bounced", "opted_out"])
    contacts = load_contacts(status if status != "All" else None)

    if contacts:
        df = pd.DataFrame([
            {
                "ID": c.id,
                "Name": f"{c.first_name or ''} {c.last_name or ''}".strip(),
                "Email": c.email,
                "Title": c.title,
                "Company": c.company,
                "LinkedIn": c.linkedin_url,
                "Status": c.status,
                "Source": c.source,
                "Notes": c.notes,
            }
            for c in contacts
        ])
        st.dataframe(df, use_container_width=True)
        st.caption(f"Showing {len(contacts)} contacts")
    else:
        st.info("No contacts found.")

# -------------------- Add Contact --------------------
elif page == "Add Contact":
    st.title("➕ Add New Contact")

    with st.form("add_contact_form"):
        col1, col2 = st.columns(2)
        first_name = col1.text_input("First Name *")
        last_name = col2.text_input("Last Name *")
        email = st.text_input("Email *")
        title = st.text_input("Job Title")
        company = st.text_input("Company")
        linkedin = st.text_input("LinkedIn URL")
        notes = st.text_area("Notes")
        find_email = st.checkbox("Try to find email with Hunter (if email empty)")

        submitted = st.form_submit_button("Add Contact")

        if submitted:
            if not first_name or not last_name:
                st.error("First name and last name required")
            else:
                session = get_session()
                # Check duplicate
                existing = None
                if email:
                    existing = session.query(Contact).filter(Contact.email == email).first()

                if existing:
                    st.warning("Contact with this email already exists")
                else:
                    final_email = email
                    source = "manual"

                    if not final_email and find_email:
                        finder = EmailFinder()
                        result = finder.find_email(first_name, last_name, company=company)
                        if result and result.get("email"):
                            final_email = result["email"]
                            source = "hunter"
                            if not title:
                                title = result.get("title")
                            st.success(f"Email found via Hunter: {final_email}")
                        else:
                            st.warning("Could not find email. Saving without email.")

                    contact = Contact(
                        first_name=first_name,
                        last_name=last_name,
                        email=final_email or None,
                        title=title,
                        company=company,
                        linkedin_url=linkedin,
                        source=source,
                        status="new",
                        notes=notes,
                    )
                    session.add(contact)
                    session.commit()
                    st.success(f"Contact added: {first_name} {last_name}")
                session.close()

# -------------------- Draft & Approve --------------------
elif page == "Draft & Approve":
    st.title("✍️ Draft & Approve Emails")

    session = get_session()
    new_contacts = session.query(Contact).filter(Contact.status == "new").filter(Contact.email.isnot(None)).all()
    drafted_contacts = session.query(Contact).filter(Contact.status == "drafted").all()
    session.close()

    tab1, tab2 = st.tabs(["Create Drafts", "Approve Drafts"])

    with tab1:
        st.subheader(f"New contacts ready for drafting ({len(new_contacts)})")
        if not new_contacts:
            st.info("No new contacts with email.")
        else:
            selected = st.multiselect(
                "Select contacts to draft",
                options=[c.id for c in new_contacts],
                format_func=lambda x: next(
                    f"{c.first_name} {c.last_name} ({c.email})" for c in new_contacts if c.id == x
                ),
            )
            if st.button("Generate Drafts with AI (Groq)", type="primary"):
                if not selected:
                    st.warning("Select at least one contact")
                else:
                    drafter = LLMDrafter()
                    session = get_session()
                    progress = st.progress(0)
                    for i, cid in enumerate(selected):
                        contact = session.query(Contact).filter(Contact.id == cid).first()
                        if contact:
                            draft = drafter.draft_cold_email({
                                "first_name": contact.first_name,
                                "last_name": contact.last_name,
                                "title": contact.title,
                                "company": contact.company,
                            })
                            log = EmailLog(
                                contact_id=contact.id,
                                email_type="initial",
                                subject=draft["subject"],
                                body=draft["body"],
                                status="draft",
                            )
                            session.add(log)
                            contact.status = "drafted"
                        progress.progress((i + 1) / len(selected))
                    session.commit()
                    session.close()
                    st.success(f"Created {len(selected)} drafts!")
                    st.rerun()

    with tab2:
        st.subheader(f"Drafts waiting for approval ({len(drafted_contacts)})")
        if not drafted_contacts:
            st.info("No drafts pending.")
        else:
            for contact in drafted_contacts:
                session = get_session()
                log = (
                    session.query(EmailLog)
                    .filter(EmailLog.contact_id == contact.id)
                    .filter(EmailLog.status == "draft")
                    .order_by(EmailLog.id.desc())
                    .first()
                )
                session.close()

                if log:
                    with st.expander(f"{contact.first_name} {contact.last_name} — {contact.company}"):
                        st.write(f"**To:** {contact.email}")
                        st.write(f"**Subject:** {log.subject}")
                        st.text_area("Body", log.body, height=200, key=f"body_{log.id}")

                        col1, col2, col3 = st.columns(3)
                        if col1.button("✅ Approve", key=f"approve_{log.id}"):
                            session = get_session()
                            log2 = session.query(EmailLog).filter(EmailLog.id == log.id).first()
                            contact2 = session.query(Contact).filter(Contact.id == contact.id).first()
                            log2.status = "approved"
                            contact2.status = "approved"
                            session.commit()
                            session.close()
                            st.success("Approved!")
                            st.rerun()

                        if col2.button("🔄 Regenerate", key=f"regen_{log.id}"):
                            drafter = LLMDrafter()
                            new_draft = drafter.draft_cold_email({
                                "first_name": contact.first_name,
                                "title": contact.title,
                                "company": contact.company,
                            })
                            session = get_session()
                            log2 = session.query(EmailLog).filter(EmailLog.id == log.id).first()
                            log2.subject = new_draft["subject"]
                            log2.body = new_draft["body"]
                            session.commit()
                            session.close()
                            st.success("Regenerated!")
                            st.rerun()

                        if col3.button("❌ Reject", key=f"reject_{log.id}"):
                            session = get_session()
                            log2 = session.query(EmailLog).filter(EmailLog.id == log.id).first()
                            contact2 = session.query(Contact).filter(Contact.id == contact.id).first()
                            log2.status = "rejected"
                            contact2.status = "new"
                            session.commit()
                            session.close()
                            st.warning("Rejected")
                            st.rerun()

# -------------------- Send Emails --------------------
elif page == "Send Emails":
    st.title("📤 Send Approved Emails")

    session = get_session()
    approved = session.query(Contact).filter(Contact.status == "approved").all()
    session.close()

    sender = EmailSender()
    sent_today = sender.count_sent_today()
    st.info(f"Sent today: {sent_today} / {DAILY_EMAIL_LIMIT}")

    if not approved:
        st.warning("No approved emails ready to send.")
    else:
        st.write(f"**{len(approved)}** emails ready")
        dry_run = st.checkbox("Dry Run (do not actually send)", value=True)

        if st.button("Send Approved Emails", type="primary"):
            progress = st.progress(0)
            success = 0
            for i, contact in enumerate(approved):
                session = get_session()
                log = (
                    session.query(EmailLog)
                    .filter(EmailLog.contact_id == contact.id)
                    .filter(EmailLog.status == "approved")
                    .order_by(EmailLog.id.desc())
                    .first()
                )
                session.close()

                if log:
                    ok = sender.send(
                        to_email=contact.email,
                        subject=log.subject,
                        body=log.body,
                        contact_id=contact.id,
                        email_type="initial",
                        dry_run=dry_run,
                    )
                    if ok:
                        success += 1
                progress.progress((i + 1) / len(approved))

            st.success(f"Processed {success} emails")
            st.rerun()

# -------------------- Import CSV --------------------
elif page == "Import CSV":
    st.title("📥 Import Contacts from CSV")
    st.markdown("""
    CSV should have columns (header required):  
    `first_name, last_name, email, title, company, linkedin_url`
    """)

    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)
        st.dataframe(df.head())

        if st.button("Import to Database"):
            session = get_session()
            added = 0
            skipped = 0
            for _, row in df.iterrows():
                email = row.get("email")
                if pd.isna(email) or not email:
                    skipped += 1
                    continue
                existing = session.query(Contact).filter(Contact.email == str(email).strip()).first()
                if existing:
                    skipped += 1
                    continue
                contact = Contact(
                    first_name=str(row.get("first_name", "")).strip() if not pd.isna(row.get("first_name")) else "",
                    last_name=str(row.get("last_name", "")).strip() if not pd.isna(row.get("last_name")) else "",
                    email=str(email).strip(),
                    title=str(row.get("title", "")).strip() if not pd.isna(row.get("title")) else "",
                    company=str(row.get("company", "")).strip() if not pd.isna(row.get("company")) else "",
                    linkedin_url=str(row.get("linkedin_url", "")).strip() if not pd.isna(row.get("linkedin_url")) else "",
                    source="csv",
                    status="new",
                )
                session.add(contact)
                added += 1
            session.commit()
            session.close()
            st.success(f"Imported {added} contacts. Skipped {skipped}.")

# -------------------- Settings --------------------
elif page == "Settings":
    st.title("⚙️ Settings & Info")
    st.markdown(f"""
    ### Current Configuration
    - **Student Name:** {STUDENT_NAME}
    - **Daily Email Limit:** {DAILY_EMAIL_LIMIT}
    - **Database:** SQLite (`data/crm.db`)

    ### Free APIs Used
    - **LLM:** Groq (Llama 3.1)
    - **Email Finder:** Hunter.io (free tier)
    - **Email Sending:** Gmail SMTP

    ### How to get free keys
    1. **Groq** → https://console.groq.com/keys  
    2. **Hunter** → https://hunter.io/api-keys (free plan available)
    3. **Gmail App Password** → Google Account → Security → 2-Step Verification → App passwords
    """)

    st.warning("Never commit your real `.env` file to GitHub.")