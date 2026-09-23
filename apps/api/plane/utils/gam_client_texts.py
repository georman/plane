# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: everything a client reads (approval emails, reminders, the
# approval page) in the client's language (Customer.language). Placeholders
# are filled with str.format; values are HTML-escaped by the caller.

TEXTS = {
    "el": {
        "greeting": "Γεια σας,",
        "thanks": "Ευχαριστούμε,",
        "email_subject": "Έγκριση: {name} – {brand}",
        "email_intro": "Η εργασία <strong>«{name}»</strong> είναι έτοιμη για την έγκρισή σας.",
        "email_intro_batch": "Η εργασία <strong>«{name}»</strong> είναι έτοιμη για την έγκρισή σας ({count} προτάσεις).",
        "email_files_attached": "Θα βρείτε τα αρχεία συνημμένα: {files}.",
        "email_files_more": " Άλλα {count} αρχεία θα τα δείτε στη σελίδα έγκρισης.",
        "email_files_page": "Τα αρχεία θα τα δείτε στη σελίδα έγκρισης.",
        "email_button": "Δείτε και εγκρίνετε",
        "email_howto": "Στη σελίδα που θα ανοίξει μπορείτε να πατήσετε <strong>Έγκριση</strong> ή <strong>Ζητώ αλλαγές</strong> και να μας γράψετε τι θέλετε να αλλάξει.",
        "email_howto_batch": "Στη σελίδα που θα ανοίξει θα δείτε όλες τις προτάσεις. Εγκρίνετε ή ζητήστε αλλαγές για κάθε μία, ή πατήστε <strong>Έγκριση όλων</strong>.",
        "email_link_note": "Ο σύνδεσμος είναι προσωπικός και ισχύει μόνο για αυτό το μήνυμα.",
        "reminder_subject": "Υπενθύμιση έγκρισης: {name} – {brand}",
        "reminder_intro": "Σας υπενθυμίζουμε ότι η εργασία <strong>«{name}»</strong> περιμένει την έγκρισή σας.",
        "page_waiting": "Η εργασία είναι έτοιμη για την έγκρισή σας.",
        "page_waiting_batch": "Δείτε κάθε πρόταση και εγκρίνετε ή ζητήστε αλλαγές.",
        "no_files": "Δεν υπάρχουν συνημμένα αρχεία.",
        "approve": "✓ Έγκριση",
        "approve_all": "✓ Έγκριση όλων",
        "request_changes": "Ζητώ αλλαγές",
        "changes_label": "Γράψτε μας τι θέλετε να αλλάξει:",
        "send_changes": "Αποστολή αλλαγών",
        "comment_label": "Έχετε κάποια ερώτηση ή σχόλιο; (χωρίς έγκριση ή αλλαγές)",
        "send_comment": "Αποστολή σχολίου",
        "need_note": "Γράψτε μας τι θέλετε να αλλάξει.",
        "need_comment": "Γράψτε το σχόλιό σας.",
        "decided_approved": "✓ Εγκρίθηκε",
        "decided_changes": "✏️ Ζητήθηκαν αλλαγές",
        "remaining": "Απομένουν {count} προτάσεις.",
        "invalid_title": "Ο σύνδεσμος δεν ισχύει",
        "invalid_text": "Ο σύνδεσμος έχει λήξει, αντικαταστάθηκε από νεότερο email, ή δεν είναι σωστός. Χρησιμοποιήστε τον σύνδεσμο από το πιο πρόσφατο email μας.",
        "answered_title": "Έχετε ήδη απαντήσει",
        "answered_text": "Για την εργασία «{name}» έχουμε ήδη την απάντησή σας ({when}). Ευχαριστούμε!",
        "moved_title": "Η εργασία έχει προχωρήσει",
        "moved_text": "Η εργασία «{name}» δεν περιμένει πλέον έγκριση. Αν χρειάζεστε κάτι, επικοινωνήστε μαζί μας.",
        "done_approved_title": "Ευχαριστούμε για την έγκριση!",
        "done_approved_text": "Προχωράμε στο επόμενο βήμα και θα σας ενημερώσουμε.",
        "done_changes_title": "Λάβαμε τις αλλαγές σας",
        "done_changes_text": "Θα κάνουμε τις διορθώσεις και θα σας στείλουμε νέα πρόταση.",
        "done_comment_title": "Λάβαμε το σχόλιό σας",
        "done_comment_text": "Θα σας απαντήσουμε σύντομα. Μπορείτε να χρησιμοποιήσετε ξανά τον ίδιο σύνδεσμο για την έγκριση.",
    },
    "en": {
        "greeting": "Hello,",
        "thanks": "Thank you,",
        "email_subject": "Approval: {name} – {brand}",
        "email_intro": "<strong>“{name}”</strong> is ready for your approval.",
        "email_intro_batch": "<strong>“{name}”</strong> is ready for your approval ({count} proposals).",
        "email_files_attached": "The files are attached: {files}.",
        "email_files_more": " {count} more files are on the approval page.",
        "email_files_page": "You will find the files on the approval page.",
        "email_button": "Review and approve",
        "email_howto": "On the page that opens you can press <strong>Approve</strong> or <strong>Request changes</strong> and tell us what to change.",
        "email_howto_batch": "The page shows every proposal. Approve or request changes for each one, or press <strong>Approve all</strong>.",
        "email_link_note": "This link is personal and only valid for this email.",
        "reminder_subject": "Approval reminder: {name} – {brand}",
        "reminder_intro": "A friendly reminder that <strong>“{name}”</strong> is waiting for your approval.",
        "page_waiting": "This is ready for your approval.",
        "page_waiting_batch": "Review each proposal and approve it or request changes.",
        "no_files": "No files attached.",
        "approve": "✓ Approve",
        "approve_all": "✓ Approve all",
        "request_changes": "Request changes",
        "changes_label": "Tell us what you would like changed:",
        "send_changes": "Send changes",
        "comment_label": "A question or comment? (does not approve or request changes)",
        "send_comment": "Send comment",
        "need_note": "Please tell us what you would like changed.",
        "need_comment": "Please write your comment.",
        "decided_approved": "✓ Approved",
        "decided_changes": "✏️ Changes requested",
        "remaining": "{count} proposals left.",
        "invalid_title": "This link is not valid",
        "invalid_text": "The link has expired, was replaced by a newer email, or is incorrect. Please use the link in our most recent email.",
        "answered_title": "You have already answered",
        "answered_text": "We already have your answer for “{name}” ({when}). Thank you!",
        "moved_title": "This has moved on",
        "moved_text": "“{name}” is no longer waiting for approval. If you need anything, please contact us.",
        "done_approved_title": "Thank you for your approval!",
        "done_approved_text": "We are moving on to the next step and will keep you posted.",
        "done_changes_title": "We received your changes",
        "done_changes_text": "We will make the corrections and send you a new version.",
        "done_comment_title": "We received your comment",
        "done_comment_text": "We will get back to you soon. You can use the same link again to approve.",
    },
}


def client_language(issue):
    """The language of the customer linked to this work item (Greek by default)."""
    from plane.db.models import IssueCustomerService

    link = IssueCustomerService.objects.filter(issue=issue).select_related("customer").first()
    language = getattr(link.customer, "language", "el") if link else "el"
    return language if language in TEXTS else "el"


def texts(language):
    return TEXTS.get(language, TEXTS["el"])
