# QR Code Tracking - Usage Examples

This document shows how to generate QR codes with optional UTM tracking parameters.

## Basic QR Code (No Tracking)

**Use for:** Physical locations where source is obvious (stores, bulletin boards)

```
Simple URL without tracking:
https://esx.ddns.net/console/recruitment/qr-code/

Generated QR URL:
https://esx.ddns.net/console/recruitment/candidato/?org=bourbon-shopping
```

## Tracked Campaign QR Codes

**Use for:** Email, social media, digital marketing, events where we want to know effectiveness

### 1. Email Marketing Campaign

```
Link to QR page WITH tracking params:
https://esx.ddns.net/console/recruitment/qr-code/?
  utm_source=email
  &utm_medium=newsletter
  &utm_campaign=recruitment_jul2026
  &utm_content=recruitment_drive
  &qr_id=email_jul_newsletter_001

Generated QR URL will be:
https://esx.ddns.net/console/recruitment/candidato/?
  org=bourbon-shopping
  &utm_source=email
  &utm_medium=newsletter
  &utm_campaign=recruitment_jul2026
  &utm_content=recruitment_drive
  &qr_id=email_jul_newsletter_001
```

### 2. Flyer at Physical Store

```
Link to QR page for store 5:
https://esx.ddns.net/console/recruitment/qr-code/loja/5/?
  utm_source=flyer
  &utm_medium=print
  &utm_campaign=bourbon_street_recruitment
  &utm_content=reception_area
  &qr_id=flyer_bourbon_store5_reception_001

Generated QR URL will be:
https://esx.ddns.net/console/recruitment/candidato/?
  org=bourbon-shopping
  &store=5
  &utm_source=flyer
  &utm_medium=print
  &utm_campaign=bourbon_street_recruitment
  &utm_content=reception_area
  &qr_id=flyer_bourbon_store5_reception_001
```

### 3. Job Fair Event

```
Link to QR page:
https://esx.ddns.net/console/recruitment/qr-code/?
  utm_source=job_fair
  &utm_medium=event
  &utm_campaign=cpf_convention_2026
  &utm_content=booth_3
  &qr_id=jobfair_cpf_booth3_001

Generated QR URL:
https://esx.ddns.net/console/recruitment/candidato/?
  org=bourbon-shopping
  &utm_source=job_fair
  &utm_medium=event
  &utm_campaign=cpf_convention_2026
  &utm_content=booth_3
  &qr_id=jobfair_cpf_booth3_001
```

### 4. Social Media Campaign (LinkedIn)

```
Link to QR page:
https://esx.ddns.net/console/recruitment/qr-code/?
  utm_source=linkedin
  &utm_medium=social_media
  &utm_campaign=recruiting_drive_2026
  &utm_content=linkedin_post
  &qr_id=social_linkedin_recruiting_2026

Generated QR URL:
https://esx.ddns.net/console/recruitment/candidato/?
  org=bourbon-shopping
  &utm_source=linkedin
  &utm_medium=social_media
  &utm_campaign=recruiting_drive_2026
  &utm_content=linkedin_post
  &qr_id=social_linkedin_recruiting_2026
```

### 5. Billboard/Outdoor Advertising

```
Link to QR page:
https://esx.ddns.net/console/recruitment/qr-code/?
  utm_source=billboard
  &utm_medium=outdoor_advertising
  &utm_campaign=highway_405_recruitment
  &utm_content=billboard_001
  &qr_id=billboard_highway405_001

Generated QR URL:
https://esx.ddns.net/console/recruitment/candidato/?
  org=bourbon-shopping
  &utm_source=billboard
  &utm_medium=outdoor_advertising
  &utm_campaign=highway_405_recruitment
  &utm_content=billboard_001
  &qr_id=billboard_highway405_001
```

## Parameter Definitions

### Standard UTM Parameters (Google Analytics)

| Parameter | Example | Description |
|-----------|---------|-------------|
| `utm_source` | email, linkedin, flyer, billboard, job_fair | Where the traffic came from (channel) |
| `utm_medium` | newsletter, social_media, print, event | Type of marketing medium |
| `utm_campaign` | recruitment_jul2026 | Name of the campaign |
| `utm_content` | recruitment_drive, booth_3, store_05 | Variant or specific content/location |
| `utm_term` | (optional) | Search term or other detail |
| `qr_id` | email_jul_store5_001 | Unique QR variant identifier |

### Recommended Naming Conventions

**utm_source (Channel):**
- `email` - Email marketing
- `social_media` / `linkedin` / `instagram` - Social platforms
- `flyer` - Printed flyers
- `billboard` - Outdoor advertising
- `job_fair` - Job fairs and events
- `referral` - Employee referrals

**utm_medium (Type):**
- `email_campaign`, `newsletter` - Email types
- `social_media`, `social_post` - Social posts
- `print`, `print_material` - Printed materials
- `outdoor_advertising`, `billboard` - Outdoor ads
- `event`, `job_fair_booth` - Event marketing

**utm_campaign (Campaign Name):**
- Format: `{purpose}_{month}{year}` or `{purpose}_{descriptor}`
- Examples: `recruitment_jul2026`, `bourbon_street_recruitment`, `cpf_convention_2026`
- Should be human-readable and consistent

**utm_content (Specific Variant):**
- Format: `{location}_{identifier}` or `{variation_name}`
- Examples: `store_05`, `booth_3`, `reception_area`, `billboard_001`
- Helps differentiate multiple QR codes from same campaign

**qr_id (Unique ID):**
- Format: `{channel}_{campaign_short}_{variant}_{number}`
- Examples: `email_jul_store5_001`, `flyer_bourbon_st_reception_001`
- Used for tracking specific physical QR codes

## Using in Different Contexts

### 1. In Email Campaigns

Add link/QR code to email:
```html
<p>Scan this QR code or click below to apply:</p>
<img src="qr_code.png" alt="Scan to apply" />
<a href="https://esx.ddns.net/console/recruitment/qr-code/?
  utm_source=email&utm_medium=newsletter&utm_campaign=recruitment_jul2026&qr_id=email_jul_001">
  Click here to apply
</a>
```

### 2. On Physical Flyers

Print QR code with metadata:
```
╔═══════════════════════════════════════════╗
║  TRABALHE COM A GENTE!                    ║
║  Bourbon Shopping                          ║
║                                            ║
║  ┌─────────────────┐                      ║
║  │   [QR CODE]     │  utm_source=flyer    ║
║  │                 │  campaign=bourbon_... ║
║  │ Scan to apply!  │  content=store_05    ║
║  └─────────────────┘                      ║
╚═══════════════════════════════════════════╝
```

### 3. In Social Media Posts

Caption with tracking:
```
🎯 Join our team!

Scan the QR code or click the link:
[Link to QR page with utm_source=linkedin, utm_campaign=recruiting_drive_2026]

#hiring #recruitment #bourbonshopping
```

### 4. In Job Fair Booths

Print multiple QR variants:
```
Booth #3 - Booth #4 - Booth #5
[QR 1]   [QR 2]   [QR 3]
booth_3  booth_4  booth_5
```

## Future: Campaign Template Management

After Phase 2 implementation, you'll be able to:

1. Create reusable campaign templates in console
2. Generate multiple QR variants automatically
3. Download as batch (ZIP with labels)
4. Track performance in analytics dashboard

For now, you can:
✅ Generate QR codes with parameters manually
✅ Use consistent naming conventions
✅ Track in external analytics tool (Google Analytics)

## Testing

### Test Simple QR (No Tracking)

1. Go to: `https://esx.ddns.net/console/recruitment/qr-code/`
2. Scan QR code → Should go to: `...candidato/?org=bourbon-shopping`
3. No utm parameters

### Test Tracked QR (Email Campaign)

1. Go to: `https://esx.ddns.net/console/recruitment/qr-code/?utm_source=email&utm_campaign=test_jul2026&qr_id=test_001`
2. Scan QR code → Should go to: `...candidato/?org=bourbon-shopping&utm_source=email&utm_campaign=test_jul2026&qr_id=test_001`
3. Check URL bar → Parameters should be present

### Test Store-Specific QR (Flyer)

1. Go to: `https://esx.ddns.net/console/recruitment/qr-code/loja/5/?utm_source=flyer&utm_content=store_05`
2. Scan QR code → Should have: `store=5` and utm parameters
3. Store name should auto-fill utm_content if not provided

## Notes

- **Backward Compatible:** Simple QR codes still work (no changes needed)
- **Optional:** Tracking parameters are optional (for non-tracked usage)
- **Future Enhancement:** Campaign templates will automate this (Phase 2)
- **Analytics:** Parameters visible in candidate signup URLs for basic tracking
- **Full Analytics:** Coming in Phase 2 with CampaignTemplate + AcquisitionSource models
