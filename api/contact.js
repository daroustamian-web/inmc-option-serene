export default async function handler(req, res) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { firstName, lastName, email, phone, interest, message } = req.body;
  if (!firstName || !email) return res.status(400).json({ error: 'Name and email required' });

  const GHL_TOKEN = 'pit-903b7684-7f90-4b74-b075-b830a4260178';
  const LOCATION_ID = 'x8il6XPJdeSXlgJFFiCJ';

  try {
    // 1. Create/upsert contact in GHL
    const contactRes = await fetch('https://services.leadconnectorhq.com/contacts/upsert', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${GHL_TOKEN}`,
        'Content-Type': 'application/json',
        'Version': '2021-07-28'
      },
      body: JSON.stringify({
        locationId: LOCATION_ID,
        firstName,
        lastName: lastName || '',
        email,
        phone: phone || '',
        tags: ['website lead', 'contact form'],
        source: 'Website Contact Form',
        customFields: [
          { key: 'contact.service_interest', field_value: interest || 'Not specified' }
        ]
      })
    });

    const contactData = await contactRes.json();
    const contactId = contactData?.contact?.id;

    // 2. Fire GHL webhook with full data (triggers workflow with all fields)
    await fetch('https://services.leadconnectorhq.com/hooks/x8il6XPJdeSXlgJFFiCJ/webhook-trigger/915eaf0a-9baf-4e1b-b704-ddeb8571abd6', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        firstName,
        lastName: lastName || '',
        email,
        phone: phone || '',
        service: interest || 'Not specified',
        message: message || '',
        source: 'Website Contact Form',
        contactId
      })
    }).catch(() => {});

    // 3. Add a note with the message if contact was created
    if (contactId && message) {
      await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}/notes`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${GHL_TOKEN}`,
          'Content-Type': 'application/json',
          'Version': '2021-07-28'
        },
        body: JSON.stringify({
          body: `Website Contact Form:\nInterest: ${interest || 'Not specified'}\nMessage: ${message}`
        })
      });
    }

    // 3. Send email notification to the clinic
    const emailBody = `
New website inquiry from ${firstName} ${lastName || ''}

Email: ${email}
Phone: ${phone || 'Not provided'}
Interest: ${interest || 'Not specified'}

Message:
${message || 'No message provided'}

---
This contact has been added to GoHighLevel with tags: Website Lead, Contact Form
    `.trim();

    await fetch('https://services.leadconnectorhq.com/conversations/messages', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${GHL_TOKEN}`,
        'Content-Type': 'application/json',
        'Version': '2021-07-28'
      },
      body: JSON.stringify({
        type: 'Email',
        locationId: LOCATION_ID,
        contactId,
        subject: `New Website Inquiry: ${interest || 'General'} — ${firstName} ${lastName || ''}`,
        message: emailBody,
        emailTo: 'info@dramaliyasantiago.com'
      })
    }).catch(() => {}); // Don't fail the whole request if email notification fails

    return res.status(200).json({ success: true, contactId });
  } catch (err) {
    console.error('GHL API error:', err);
    return res.status(500).json({ error: 'Failed to submit. Please call (626) 714-7400.' });
  }
}
