# Tanshu API Error Codes Reference

## Error Code Descriptions

The Gold Price Predictor now includes comprehensive error handling for the Tanshu API. Here are all possible error codes and their meanings:

### 🚨 API Error Codes

| Error Code | Chinese Description | English Description | Solution |
|------------|-------------------|-------------------|----------|
| **10001** | 错误的请求KEY | Invalid API Key | Check your API key is correct |
| **10002** | 该KEY无请求权限 | Key has no request permission | Contact API provider for permissions |
| **10003** | KEY过期 | API Key expired | Renew your API subscription |
| **10004** | 未知的请求源 | Unknown request source | Check API endpoint URL |
| **10005** | 被禁止的IP | Banned IP address | Contact support, IP may be blocked |
| **10006** | 被禁止的KEY | Banned API Key | API key is blacklisted, get new key |
| **10007** | 请求超过次数限制 | Request limit exceeded | Wait for quota reset or upgrade plan |
| **10008** | 接口维护 | API under maintenance | Wait for maintenance to complete |

### 📊 Error Display Features

The GUI now includes a dedicated **"Error Status & Diagnostics"** section in the API Info tab that shows:

1. **Error Status**: ✅ No errors or ❌ Error detected
2. **Error Code**: The specific numeric code from the API
3. **Description**: Bilingual description (Chinese + English explanation)

### 🔧 Error Handling Behavior

#### ✅ **When Everything Works:**
- Error Status: "✅ No errors detected" (green)
- Error Code: "None"
- Description: "All systems operational"

#### ❌ **When API Errors Occur:**
- Error Status: "❌ API Error Detected" (red)
- Error Code: Shows the specific error number (e.g., "10007")
- Description: Shows both Chinese and English explanation

#### ⚠️ **When Network Errors Occur:**
- Error Status: "❌ General Error" (red)
- Error Code: "N/A"
- Description: Network/connection error details

### 🎯 **Usage Benefits:**

1. **Immediate Diagnosis**: Know exactly what's wrong with API calls
2. **Quota Management**: Error 10007 tells you when you've hit request limits
3. **Troubleshooting**: Clear descriptions help solve problems quickly
4. **Bilingual Support**: Chinese error messages with English explanations
5. **Real-time Updates**: Error status updates automatically

### 🔄 **Error Recovery:**

- Errors are automatically cleared when the next successful API call is made
- Manual refresh button can be used to retry after fixing issues
- Auto-refresh will continue attempting to recover from errors

### 💡 **Common Issues & Solutions:**

**Error 10007 (Request Limit Exceeded):**
- Current limit: 600 requests/month
- Optimal interval: ~52 minutes between requests
- Solution: Wait for monthly quota reset or use manual refresh sparingly

**Error 10003 (Key Expired):**
- API subscription has expired
- Solution: Renew Tanshu API subscription

**Error 10001 (Invalid Key):**
- API key is incorrect or malformed
- Solution: Check API key in gold_predictor.py

This enhanced error handling makes the Gold Price Predictor much more user-friendly and helps quickly identify and resolve any API-related issues!
