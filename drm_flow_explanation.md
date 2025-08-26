# DRM/Widevine Flow Explanation: Hoopla Digital Implementation

## Executive Summary

Your webapp implements a multi-step DRM protection flow using Google Widevine with castLabs' DRMtoday as the license service provider. The system uses JWT-based upfront authentication tokens to authorize users before granting licenses for encrypted content playback.

## Key Components

### 1. **Service Architecture**
- **Content Provider**: Hoopla Digital (digital library streaming service)
- **DRM System**: Google Widevine (L3 browser implementation)
- **License Service**: castLabs DRMtoday
- **Encryption Standard**: Common Encryption (CENC) with AES-CTR
- **Content Format**: MPEG-DASH with MPD manifests

### 2. **Authentication Layers**
- **User Authentication**: Bearer token for Hoopla API access
- **DRM Authentication**: JWT-based upfront auth token for license requests
- **Custom Data**: Base64-encoded user/session metadata

## Detailed Flow Analysis

### Step 1: Upfront Authentication Token Request

**Request URL**: `https://patron-api-gateway.hoopladigital.com/license/castlabs/upfront-auth-tokens/...`

**Purpose**: Obtain a time-limited JWT token that pre-authorizes the user for DRM license acquisition

**Key Elements**:
- **Bearer Token**: User's session authentication (`c5e79544-1808-4df1-ae56-5849e28ef2ff`)
- **Resource ID**: Content identifier (`mcm_9781250210401`)
- **User ID**: `13914483`
- **Session ID**: `423234040`

**Response (Decoded JWT)**:
```json
{
  "optData": {
    "userId": "13914483",
    "merchant": "hoopla",
    "sessionId": "423234040"
  },
  "crt": [{
    "accountingId": "423234040",
    "assetId": "mcm_9781250210401:932ae92f716ade1a7c9622066c491d35",
    "profile": {
      "rental": {
        "absoluteExpiration": "2025-09-11T01:40:21.672Z",
        "playDuration": 1388177723
      }
    },
    "message": "access granted",
    "outputProtection": {
      "digital": false,
      "analogue": false,
      "enforce": false
    },
    "storeLicense": true
  }],
  "iat": 1756166643,
  "jti": "+AAPMME/VxlWjVHNLE6bSA=="
}
```

**Key Insights**:
- Token includes rental period (expires Sept 11, 2025)
- Play duration limited to ~16 days (1388177723 ms)
- Output protection disabled (allows playback without HDCP)
- License storage enabled for offline playback capability

### Step 2: Manifest Retrieval

**Request URL**: `https://dash.hoopladigital.com/mcm_9781250210401/Manifest.mpd`

**Purpose**: Obtain the DASH manifest containing encryption information and content structure

**Key Manifest Elements**:
```xml
- Content Duration: 16h 6m 47s (audiobook)
- Encryption: CENC with default KID
- DRM Systems: PlayReady and Widevine
- Content Key ID: ab682fb9-4fa9-8bb2-b083-88884dc08edd
- License URLs embedded in manifest
```

**Protection Information**:
- **Widevine PSSH**: Contains initialization data for license request
- **PlayReady Header**: Alternative DRM system support
- **castLabs Metadata**: Asset and variant identifiers

### Step 3: License Acquisition

**Request URL**: `https://lic.drmtoday.com/license-proxy-widevine/cenc/`

**Purpose**: Exchange Widevine license request for decryption keys

**Request Headers**:
- **x-dt-auth-token**: The JWT from Step 1 (proves pre-authorization)
- **dt-custom-data**: Base64-encoded user context
  ```json
  {
    "userId": 13914483,
    "sessionId": "423234040",
    "merchant": "hoopla"
  }
  ```

**Request Body**: Binary Widevine license request containing:
- Encrypted content key ID
- Device certificate
- Security level information
- DRM system capabilities

**Response Structure**:
```json
{
  "status": "OK",
  "license": "[Base64 encoded Widevine license]",
  "service_version_info": {
    "license_sdk_version": "19.10.1",
    "license_service_version": "DRMtoday"
  },
  "supported_tracks": [{
    "type": "AUDIO",
    "key_id": "q2gvuU+pi7Kwg4iITcCO3Q=="
  }],
  "message_type": "LICENSE_REQUEST",
  "platform": "windows"
}
```

## Security Mechanisms

### 1. **Token Lifecycle**
- Upfront auth tokens valid for ~10 minutes
- Single-use design (token invalidated after license request)
- JWT signature verification using HS512 algorithm

### 2. **Content Protection**
- Content encrypted at rest using CENC
- Keys never transmitted in clear text
- License bound to specific device/session

### 3. **Access Control**
- Multi-tier authentication (user + DRM)
- Time-based restrictions (rental period)
- Play duration limits

## Flow Diagram

```
User Browser                 Hoopla API              DRMtoday            Content CDN
    |                            |                        |                    |
    |--Login & Get Bearer Token->|                        |                    |
    |                            |                        |                    |
    |--Request Auth Token------->|                        |                    |
    |   (with Bearer token)      |                        |                    |
    |<--JWT Auth Token-----------|                        |                    |
    |                            |                        |                    |
    |--Request Manifest----------------------------------------->|
    |<--DASH MPD with PSSH---------------------------------------|
    |                            |                        |                    |
    |--Generate License Request->|                        |                    |
    |   (Widevine CDM)           |                        |                    |
    |                            |                        |                    |
    |--Send License Request------------------------------>|                    |
    |   (with JWT auth token)    |                        |                    |
    |                            |   --Verify JWT-->      |                    |
    |                            |   --Check Rights->      |                    |
    |                            |   <--Issue License--    |                    |
    |<--Widevine License---------------------------------|                    |
    |                            |                        |                    |
    |--Request Encrypted Content---------------------------------->|
    |<--Encrypted Media Segments------------------------------------|
    |                            |                        |                    |
    |--Decrypt & Play           |                        |                    |
    |   (using license keys)     |                        |                    |
```

## Business Logic Implementation

### Rental Model
- **Absolute Expiration**: Hard deadline for content access
- **Play Duration**: Total cumulative playback time allowed
- **First Play Activation**: License becomes active on first playback

### Device Management
- Licenses tied to specific devices via Widevine CDM
- Storage of licenses enables offline playback
- Token single-use prevents license sharing

### Content Segmentation
- Audio streams packaged in MP4 containers
- Segment-based delivery for adaptive streaming
- Index ranges define initialization segments

## Technical Considerations

### Browser Requirements
- Widevine CDM support (Chrome, Edge, Firefox)
- Encrypted Media Extensions (EME) API
- Media Source Extensions (MSE) for DASH playback

### Network Requirements
- HTTPS for all DRM communications
- CORS headers properly configured
- CDN support for byte-range requests

### Error Handling
- Token expiration graceful fallback
- Network failure retry logic
- License renewal before expiration

## Summary

This implementation demonstrates a robust, industry-standard DRM protection system that:

1. **Authenticates** users through multiple layers
2. **Authorizes** content access with time and usage restrictions  
3. **Encrypts** content using strong cryptography
4. **Delivers** licenses securely through trusted channels
5. **Enforces** playback restrictions at the client level

The use of JWT tokens for upfront authentication eliminates the need for DRMtoday to callback to Hoopla's servers during license requests, improving performance and reducing complexity. The token contains all necessary authorization data, cryptographically signed to prevent tampering.

This architecture balances security, performance, and user experience while meeting content protection requirements for digital library services.
