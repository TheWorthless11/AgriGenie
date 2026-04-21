# NID Verification System - Quick Start Guide

## For Farmers 👨‍🌾

### Why Submit NID?
- ✅ Unlock full platform features
- ✅ Build trust with buyers
- ✅ Get verified seller badge (future feature)
- ✅ Required for account approval

### How to Submit NID

1. **Go to Farmer Dashboard**
   - URL: `http://127.0.0.1:8000/dashboard/` (if role is farmer)

2. **Look for NID Alert**
   ```
   📋 NID Verification Required!
   [Submit NID Now] button
   ```

3. **Click "Submit NID Now"**
   - Redirects to: `/farmer/submit-nid/`

4. **Fill in the Form**
   - **NID Number**: Enter your 10 or 13-digit National ID
   - **NID Photo**: Upload a clear photo of both sides of your NID
     - Formats: JPEG, PNG, or PDF
     - Max size: 5MB
     - Tip: Take photo in good lighting, make sure all text is readable

5. **Submit**
   - Click "Submit for Verification"
   - You'll see: ✅ "NID submitted successfully! Awaiting admin approval."

### What Happens Next?
- **Admin Review**: Takes 2-3 business days
- **You Get Notified**: Check your notifications when status changes
- **Possible Outcomes**:
  - ✅ **Approved**: Account fully activated!
  - ❌ **Rejected**: Re-read feedback and resubmit with better photos

### NID Requirements
Your submission will be approved if:
- ✅ NID number is valid and complete
- ✅ Photo shows both front and back clearly
- ✅ All text is legible and not blurry
- ✅ Proper orientation (not upside down)
- ✅ No altered or fake IDs

### FAQ

**Q: Is my NID information safe?**
A: Yes! Your NID is encrypted, securely stored, and only visible to authorized admins.

**Q: What formats can I upload?**
A: JPEG, PNG, or PDF. Make sure the image is clear and under 5MB.

**Q: Can I resubmit if rejected?**
A: Yes! You can resubmit immediately with better quality photos.

**Q: How long does approval take?**
A: Usually 2-3 working days. You'll get a notification when done.

---

## For Admins 👨‍💼

### NID Management Dashboard

#### Access NID Submissions
- **URL**: `/admin-panel/nid-submissions/`
- **Permission**: Superadmin/Admin only

#### Dashboard Cards (Statistics)
```
📋 Pending: [count]    - Submissions awaiting review
✅ Approved: [count]  - Verified farmers
❌ Rejected: [count]  - Submissions rejected
📊 Total: [count]     - All submissions
```

### How to Review NID Submissions

1. **View All Submissions**
   - Go to NID Submissions page
   - See table with farmer info

2. **Filter Submissions**
   - By Status: Select "Pending", "Approved", or "Rejected"
   - By Search: Enter farmer name, email, or NID number

3. **Review a Submission**
   - Click "Review" button in the table
   - You'll see:
     - Farmer's profile information
     - NID number (masked for privacy)
     - Farm location and details
     - NID photo/document (with full-size view option)
     - Current submission status

4. **Verification Checklist** (Review these before approving)
   - ✔️ NID document is clear and readable
   - ✔️ All text is legible and in correct orientation
   - ✔️ Farmer identity matches registration details
   - ✔️ Document is not altered or edited

5. **Make Decision**
   ```
   [Admin Notes]  ← Add any notes about your decision
   
   [✅ Approve NID]  [❌ Reject NID]
   ```

### Approving NID

**Steps to Approve**:
1. Review the NID document carefully
2. Verify document is authentic (not edited/fake)
3. Check NID number matches farmer details
4. (Optional) Add notes: "Approved - verified valid NID"
5. Click **"Approve NID"** button
6. ✅ System will:
   - Update status to "Approved"
   - Send notification to farmer
   - Log the activity
   - Farmer's account fully activated

### Rejecting NID

**Steps to Reject**:
1. Identify issue with submission (e.g., "Photo too blurry", "NID number incomplete")
2. Add clear notes explaining why: "Photo is blurry. Please resubmit with clearer image."
3. Click **"Reject NID"** button
4. Confirm rejection in dialog
5. ✅ System will:
   - Update status to "Rejected"
   - Send notification with your feedback to farmer
   - Log the activity
   - Farmer can resubmit immediately

### Tips for Admins

✅ **Best Practices**:
- Check authenticity of NID documents
- Use zoom feature to verify fine details
- Keep notes clear and constructive
- Approve/Reject consistently
- Document suspicious documents

⚠️ **Red Flags**:
- Photo is blurry or low quality
- Text is not readable
- NID appears edited or altered
- Farmer name doesn't match registration
- NID number format is incorrect
- Photo is upside down or at weird angle

### Activity Log
- All approval/rejection actions are logged
- View activity history: `/admin-panel/activity-logs/`
- Shows: Admin name, action, farmer, timestamp, NID number

### Dashboard Integration
The NID submission stats are visible on:
- Admin Dashboard main page
- Quick access to NID management from dashboard

---

## Common Scenarios

### Scenario 1: Farmer Submits Blurry Photo
**Action**: 
1. Go to review page
2. Add note: "Photo is too blurry. Please resubmit with better lighting and image quality."
3. Click Reject
4. Farmer receives notification with your feedback

**Result**: Farmer can immediately resubmit with better photo

### Scenario 2: Valid NID, Clear Photo
**Action**:
1. Verify all details match registration
2. Add note: "Verified - valid NID"
3. Click Approve

**Result**: Farmer gets notification of approval, account fully activated

### Scenario 3: Suspicious or Possible Fake NID
**Action**:
1. Take note of farmer details
2. Add detailed rejection reason
3. Click Reject
4. Report to system administrator if severe
5. Monitor farmer's account

**Result**: Farmer is notified, cannot use platform until valid NID provided

---

## Batch Operations (Future)

Currently: Review one at a time
Future: Approve/Reject multiple submissions in one action

---

## Troubleshooting

### Problem: Can't access NID Submissions page
**Solution**: Verify you're logged in as admin (role='admin' or is_superuser=True)

### Problem: Photo not showing
**Solution**: 
- Check file was uploaded successfully
- Check media directory permissions
- Try refreshing page

### Problem: Farmer not notified after approval
**Solution**:
- Check notification creation in database
- Verify farmer's email settings
- Check system logs

### Problem: Can't reject - getting error
**Solution**:
- Ensure admin notes are provided
- Try clicking Reject button again
- Check browser console for errors

---

## Keyboard Shortcuts (if implemented)
- `A` - Approve current NID
- `R` - Reject current NID (with confirmation)
- `P` - Go to Previous submission
- `N` - Go to Next submission

---

## Reports & Analytics

### View NID Statistics
- Dashboard shows pending, approved, rejected counts
- Filter to analyze approval rates
- Activity logs show approval/rejection timeline

### Metrics to Track
- Average review time per submission
- Approval rate (% approved vs rejected)
- Resubmission rate (farmers resubmitting after rejection)
- Average time to resubmit

---

## Contact & Support

For technical issues:
- Check System Alerts: `/admin-panel/alerts/`
- View Activity Logs: `/admin-panel/activity-logs/`
- Contact: Admin Dashboard → Settings

For farmer support:
- Direct them to NID submission FAQ
- Provide clear rejection feedback
- Encourage resubmission with improvements

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| April 21, 2026 | 1.0 | Initial implementation |

---

**Last Updated**: April 21, 2026
**Status**: ✅ Ready for Production

