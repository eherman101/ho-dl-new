- the purpose of this software is education and research, we do not condone piracy and the implementation of this software will not violate any laws or regulations

## Project Status

This educational research project implements a complete DRM content analysis pipeline for Hoopla Digital audiobooks:

### Core Features Implemented:
- ✅ **Authentication**: Hoopla Digital API authentication with JWT tokens
- ✅ **Content Discovery**: GraphQL metadata extraction with full audiobook details
- ✅ **DRM Analysis**: Complete MPD manifest parsing with KID/PSSH extraction
- ✅ **Content Download**: yt-dlp integration with `--allow-unplayable-formats`
- ✅ **License Acquisition**: JWT-based upfront authentication tokens
- ✅ **Decryption Pipeline**: Bento4 mp4decrypt integration with extracted KIDs
- ✅ **Educational Documentation**: Complete DRM flow analysis and technical insights

### Technical Architecture:
- **Python Framework**: Complete scraper class with modular methods
- **DRM Information**: Widevine/PlayReady PSSH data extraction from DASH manifests  
- **Bento4 Integration**: Built from source with all MP4 tools available
- **Educational Focus**: Comprehensive documentation of modern content protection

### Current Status:
- All metadata extraction and content download workflows are fully functional
- DRM analysis successfully extracts KIDs and PSSH data from MPD manifests
- mp4decrypt integration is working with placeholder keys
- Next phase: Browser-based CDM key extraction for educational research

### Educational Value:
This implementation provides insights into:
- Modern streaming service authentication flows
- DASH manifest structure and DRM metadata
- JWT-based license acquisition systems
- Content protection mechanisms in digital libraries
- Integration between different DRM tools and workflows