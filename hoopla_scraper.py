#!/usr/bin/env python3
"""
Hoopla Digital Archive Scraper
Educational and research purposes only
"""

import os
import requests
import json
import subprocess
import base64
import xml.etree.ElementTree as ET
from urllib.parse import quote
from dotenv import load_dotenv
import logging
import binascii

class HooplaScraper:
    def __init__(self):
        load_dotenv('.env.secrets')
        
        self.username = os.getenv('USERNAME')
        self.password = os.getenv('PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("Username and password must be set in .env.secrets file")
        
        self.session = requests.Session()
        self.token = None
        
        # Set up headers based on the curl request
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'app': 'WWW',
            'binge-pass-external-enabled': 'true',
            'content-type': 'application/x-www-form-urlencoded',
            'device-model': '139.0.0.0',
            'device-version': 'Chrome',
            'dnt': '1',
            'hoopla-version': '4.124.2',
            'origin': 'https://www.hoopladigital.com',
            'os': 'Windows',
            'os-version': '10',
            'priority': 'u=1, i',
            'referer': 'https://www.hoopladigital.com/',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'ws-api': '2.1'
        }
        
        self.session.headers.update(self.headers)
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def login(self):
        """Authenticate with Hoopla Digital"""
        login_url = 'https://patron-api-gateway.hoopladigital.com/core/tokens'
        
        # Prepare login data
        login_data = f"username={quote(self.username)}&password={quote(self.password)}"
        
        try:
            response = self.session.post(login_url, data=login_data)
            response.raise_for_status()
            
            token_data = response.json()
            
            if token_data.get('tokenStatus') == 'SUCCESS':
                self.token = token_data.get('token')
                self.logger.info("Successfully authenticated with Hoopla Digital")
                # Add token to session headers for future requests
                self.session.headers['Authorization'] = f'Bearer {self.token}'
                return True
            else:
                self.logger.error(f"Authentication failed. Status: {token_data.get('tokenStatus')}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Login request failed: {e}")
            return False
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse login response: {e}")
            return False

    def get_user_info(self):
        """Get user account information"""
        if not self.token:
            self.logger.error("Not authenticated. Please login first.")
            return None
            
        # This is a common endpoint for user info - adjust as needed
        user_info_url = 'https://patron-api-gateway.hoopladigital.com/core/user'
        
        try:
            response = self.session.get(user_info_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get user info: {e}")
            return None

    def get_borrowed_items(self):
        """Get currently borrowed items"""
        if not self.token:
            self.logger.error("Not authenticated. Please login first.")
            return None
            
        borrowed_url = 'https://patron-api-gateway.hoopladigital.com/core/borrowed'
        
        try:
            response = self.session.get(borrowed_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get borrowed items: {e}")
            return None

    def get_audiobook_details(self, item_id):
        """Get detailed information about an audiobook using GraphQL"""
        if not self.token:
            self.logger.error("Not authenticated. Please login first.")
            return None
            
        graphql_url = 'https://patron-api-gateway.hoopladigital.com/graphql'
        
        # GraphQL query from the curl request
        graphql_query = """query GetFetchTitleDetailQuery($id: ID!, $includeDeleted: Boolean, $showHolds: Boolean = true, $showMarketingText: Boolean = false) {
  title(criteria: {id: $id, includeDeleted: $includeDeleted}) {
    abridged
    actors {
      id
      name
      __typename
    }
    artKey
    authors {
      name
      id
      __typename
    }
    bingePassType
    bisacs {
      id
      ancestors {
        id
        name
        __typename
      }
      children {
        id
        name
        parent {
          id
          name
          __typename
        }
        __typename
      }
      name
      isParent
      parent {
        id
        name
        __typename
      }
      __typename
    }
    bundledContent {
      ...BundledContentFragment
      __typename
    }
    captions {
      id
      cc
      language
      __typename
    }
    chapters {
      chapter
      duration
      ordinal
      start
      title
      __typename
    }
    childrens
    circulation {
      borrowedDate
      dueDate
      id
      isRenewable
      licenseType
      maxDue
      patron {
        id
        __typename
      }
      title {
        title
        __typename
      }
      __typename
    }
    copyright
    demo
    directors {
      name
      id
      __typename
    }
    episodes {
      artKey
      circulation {
        borrowedDate
        dueDate
        id
        isRenewable
        licenseType
        patron {
          id
          __typename
        }
        __typename
      }
      episode
      id
      lastBorrowed
      lendingMessage
      licenseType
      mediaKey
      playbackPosition {
        percentComplete
        lastPlayed
        __typename
      }
      seconds
      status
      synopsis
      subtitle
      title
      __typename
    }
    externalCatalogUrl
    favorite
    fixedLayout
    genres {
      ancestors {
        id
        name
        __typename
      }
      id
      name
      __typename
    }
    hold @include(if: $showHolds) {
      ...HoldFragment
      __typename
    }
    holdsPerCopy @include(if: $showHolds)
    id
    illustrators {
      id
      name
      __typename
    }
    isbn
    issueNumberDescription
    kind {
      name
      id
      singular
      plural
      __typename
    }
    language {
      name
      label
      id
      __typename
    }
    lastBorrowed
    lendingMessage
    licenseType
    manga
    marketingText @include(if: $showMarketingText)
    mediaKey
    mediaType
    overlay {
      ...TitleOverlayFragment
      __typename
    }
    pages
    parentalAdvisory
    patronRating {
      stars
      __typename
    }
    people {
      id
      name
      relationship
      __typename
    }
    percentComplete
    playbackPosition {
      percentComplete
      lastPlayed
      __typename
    }
    primaryArtist {
      name
      id
      similarArtists {
        id
        name
        __typename
      }
      __typename
    }
    producers {
      name
      id
      __typename
    }
    profanity
    publisher {
      id
      name
      __typename
    }
    rating
    readAlong
    readers {
      name
      id
      __typename
    }
    relatedTitles {
      ...TitleListItemFragment
      __typename
    }
    releaseDate
    reviews {
      id
      source
      quote
      __typename
    }
    seconds
    seriesNumberLabel
    series {
      id
      name
      __typename
    }
    status
    subtitle
    subtitleLanguage {
      name
      __typename
    }
    synopsis
    tags {
      id
      name
      __typename
    }
    title
    titleRating {
      totalCount
      weightedAverage
      __typename
    }
    tracks {
      ...TrackFragment
      __typename
    }
    traditionalManga
    writers {
      id
      name
      __typename
    }
    year
    zombieHoldCount @include(if: $showHolds)
    __typename
  }
}

fragment TitleOverlayFragment on TitleOverlay {
  name
  backColor
  foreColor
  __typename
}

fragment TrackFragment on Track {
  contentId
  id
  mediaKey
  name
  seconds
  segmentNumber
  __typename
}

fragment BundledContentFragment on Content {
  id
  artKey
  captions {
    cc
    __typename
  }
  circulation {
    licenseType
    __typename
  }
  episode
  episodeTitle
  issueNumberDescription
  kind {
    name
    singular
    __typename
  }
  language {
    label
    __typename
  }
  manga
  mediaKey
  overlay {
    ...TitleOverlayFragment
    __typename
  }
  pages
  parentalAdvisory
  playbackPosition {
    lastPlayed
    percentComplete
    __typename
  }
  primaryArtist {
    name
    __typename
  }
  rating
  season
  seconds
  series {
    name
    __typename
  }
  seriesNumberLabel
  synopsis
  title
  titleId
  trackCount
  tracks {
    ...TrackFragment
    __typename
  }
  traditionalManga
  year
  __typename
}

fragment HoldFragment on Hold {
  id
  position
  positionPerCopy
  reserveUntil
  snoozeUntil
  suspendDays
  suspendUntil
  status
  zombie
  __typename
}

fragment TitleListItemFragment on Title {
  id
  artKey
  issueNumberDescription
  kind {
    name
    __typename
  }
  overlay {
    ...TitleOverlayFragment
    __typename
  }
  parentalAdvisory
  primaryArtist {
    name
    __typename
  }
  releaseDate
  title
  titleId
  status
  licenseType
  __typename
  bingePassType
  holdsPerCopy
  playbackPosition {
    percentComplete
    __typename
  }
  tracks {
    segmentNumber
    __typename
  }
  zombieHoldCount
}"""
        
        # Set up GraphQL headers
        graphql_headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'apollographql-client-name': 'hoopla-www',
            'apollographql-client-version': '4.124.2',
            'authorization': f'Bearer {self.token}',
            'binge-pass-external-enabled': 'true',
            'binge-pass-internal-enabled': 'true',
            'content-type': 'application/json',
            'dnt': '1',
            'external-promos-enabled': 'true',
            'origin': 'https://www.hoopladigital.com',
            'priority': 'u=1, i',
            'referer': 'https://www.hoopladigital.com/',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'traditional-manga-enabled': 'true',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }
        
        # Prepare GraphQL payload
        payload = {
            "operationName": "GetFetchTitleDetailQuery",
            "variables": {
                "showHolds": True,
                "showMarketingText": True,
                "id": str(item_id),
                "includeDeleted": False
            },
            "query": graphql_query
        }
        
        try:
            response = self.session.post(graphql_url, json=payload, headers=graphql_headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get audiobook details for ID {item_id}: {e}")
            return None

    def archive_audiobook(self, item_id):
        """Archive a specific audiobook by ID"""
        self.logger.info(f"Archiving audiobook with ID: {item_id}")
        
        audiobook_data = self.get_audiobook_details(item_id)
        if audiobook_data:
            filename = f"audiobook_{item_id}.json"
            self.save_data(audiobook_data, filename)
            
            # Extract and log title for confirmation
            try:
                title = audiobook_data['data']['title']['title']
                self.logger.info(f"Successfully archived: {title}")
            except (KeyError, TypeError):
                self.logger.info(f"Successfully archived audiobook ID: {item_id}")
            
            return audiobook_data
        else:
            self.logger.error(f"Failed to archive audiobook ID: {item_id}")
            return None

    def get_license_blob(self, media_key, patron_id, circulation_id):
        """Get license blob for media access using Castlabs upfront auth tokens"""
        if not self.token:
            self.logger.error("Not authenticated. Please login first.")
            return None
            
        # Construct the license URL using the media key, patron ID, and circulation ID
        license_url = f'https://patron-api-gateway.hoopladigital.com/license/castlabs/upfront-auth-tokens/{media_key}/{patron_id}/{circulation_id}'
        
        # Set up license request headers
        license_headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': f'Bearer {self.token}',
            'content-type': 'application/x-www-form-urlencoded',
            'dnt': '1',
            'origin': 'https://www.hoopladigital.com',
            'priority': 'u=1, i',
            'referer': 'https://www.hoopladigital.com/',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }
        
        try:
            self.logger.info(f"Requesting license blob for media key: {media_key}")
            response = self.session.get(license_url, headers=license_headers)
            response.raise_for_status()
            
            # The response is a JWT token string, not JSON
            license_token = response.text.strip()
            if license_token:
                return {
                    'jwt_token': license_token,
                    'media_key': media_key,
                    'patron_id': patron_id,
                    'circulation_id': circulation_id,
                    'retrieved_at': response.headers.get('Date')
                }
            else:
                self.logger.error("Empty license response received")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get license blob for {media_key}: {e}")
            return None

    def get_mpd_manifest(self, media_key):
        """Get MPD manifest for media streaming"""
        if not media_key:
            self.logger.error("Media key is required to get MPD manifest")
            return None
            
        # Construct MPD manifest URL
        mpd_url = f'https://dash.hoopladigital.com/{media_key}/Manifest.mpd'
        
        # Set up MPD request headers
        mpd_headers = {
            'sec-ch-ua-platform': '"Windows"',
            'Referer': 'https://www.hoopladigital.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'DNT': '1',
            'sec-ch-ua-mobile': '?0'
        }
        
        try:
            self.logger.info(f"Requesting MPD manifest for media key: {media_key}")
            response = self.session.get(mpd_url, headers=mpd_headers)
            response.raise_for_status()
            
            # MPD is XML content, return as text
            mpd_content = response.text
            if mpd_content:
                return {
                    'mpd_content': mpd_content,
                    'media_key': media_key,
                    'mpd_url': mpd_url,
                    'retrieved_at': response.headers.get('Date'),
                    'content_type': response.headers.get('Content-Type')
                }
            else:
                self.logger.error("Empty MPD manifest response received")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get MPD manifest for {media_key}: {e}")
            return None

    def parse_mpd_manifest(self, mpd_content):
        """Parse MPD manifest to extract DRM information and KIDs"""
        try:
            root = ET.fromstring(mpd_content)
            
            # Define namespaces used in DASH manifests
            namespaces = {
                'mpd': 'urn:mpeg:dash:schema:mpd:2011',
                'cenc': 'urn:mpeg:cenc:2013'
            }
            
            # Extract content protection information
            drm_info = {
                'kids': [],
                'pssh_data': {},
                'license_urls': {},
                'default_kid': None
            }
            
            # Find ContentProtection elements
            for cp in root.findall('.//mpd:ContentProtection', namespaces):
                scheme_id = cp.get('schemeIdUri', '')
                
                # Extract KID from default_KID attribute (CENC common encryption)
                default_kid = cp.get('{urn:mpeg:cenc:2013}default_KID')
                if default_kid:
                    drm_info['default_kid'] = default_kid.replace('-', '').lower()
                    drm_info['kids'].append(drm_info['default_kid'])
                
                # Extract Widevine PSSH (UUID: edef8ba9-79d6-4ace-a3c8-27dcd51d21ed)
                if 'edef8ba9-79d6-4ace-a3c8-27dcd51d21ed' in scheme_id:
                    pssh_element = cp.find('.//cenc:pssh', namespaces)
                    if pssh_element is not None:
                        drm_info['pssh_data']['widevine'] = pssh_element.text.strip()
                
                # Extract PlayReady PSSH (UUID: 9a04f079-9840-4286-ab92-e65be0885f95)
                if '9a04f079-9840-4286-ab92-e65be0885f95' in scheme_id:
                    pssh_element = cp.find('.//cenc:pssh', namespaces)
                    if pssh_element is not None:
                        drm_info['pssh_data']['playready'] = pssh_element.text.strip()
                
                # Extract castLabs DRMtoday information
                if 'castlabs:drmtoday' in scheme_id:
                    asset_id = cp.get('{urn:castlabs:drmtoday:cenc:2014}assetId')
                    variant_id = cp.get('{urn:castlabs:drmtoday:cenc:2014}variantId')
                    if asset_id:
                        drm_info['castlabs_asset_id'] = asset_id
                    if variant_id:
                        drm_info['castlabs_variant_id'] = variant_id
                
            # Extract period-level protection if present
            for period in root.findall('.//mpd:Period', namespaces):
                for adaptation_set in period.findall('.//mpd:AdaptationSet', namespaces):
                    for cp in adaptation_set.findall('.//mpd:ContentProtection', namespaces):
                        default_kid = cp.get('cenc:default_KID')
                        if default_kid and default_kid not in drm_info['kids']:
                            kid_hex = default_kid.replace('-', '').lower()
                            drm_info['kids'].append(kid_hex)
                            if drm_info['default_kid'] is None:
                                drm_info['default_kid'] = kid_hex
            
            self.logger.info(f"Extracted DRM info: {len(drm_info['kids'])} KIDs found")
            return drm_info
            
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse MPD manifest: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error extracting DRM info from manifest: {e}")
            return None

    def get_widevine_license(self, jwt_token, pssh_data, user_id, session_id):
        """Get Widevine license from castLabs DRMtoday"""
        if not pssh_data.get('widevine'):
            self.logger.error("No Widevine PSSH data available")
            return None
            
        # Prepare custom data as described in the documentation
        custom_data = {
            "userId": int(user_id),
            "sessionId": session_id,
            "merchant": "hoopla"
        }
        custom_data_b64 = base64.b64encode(json.dumps(custom_data).encode()).decode()
        
        # DRMtoday license URL from documentation
        license_url = 'https://lic.drmtoday.com/license-proxy-widevine/cenc/'
        
        # Create a simple Widevine license request
        # In a real implementation, this would be generated by the Widevine CDM
        # For educational purposes, we'll create a basic request structure
        license_request_data = base64.b64decode(pssh_data['widevine'])
        
        headers = {
            'Content-Type': 'application/octet-stream',
            'x-dt-auth-token': jwt_token,
            'dt-custom-data': custom_data_b64,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }
        
        try:
            self.logger.info("Requesting Widevine license from DRMtoday")
            response = self.session.post(
                license_url,
                data=license_request_data,
                headers=headers
            )
            response.raise_for_status()
            
            # The response should contain the license
            license_response = response.content
            
            self.logger.info("Successfully obtained Widevine license")
            return {
                'license_data': base64.b64encode(license_response).decode(),
                'license_url': license_url,
                'custom_data': custom_data,
                'retrieved_at': response.headers.get('Date')
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get Widevine license: {e}")
            if hasattr(e.response, 'text'):
                self.logger.error(f"Response: {e.response.text}")
            return None

    def decrypt_with_mp4decrypt(self, encrypted_file_path, kid, key, output_path=None):
        """Decrypt MP4 file using Bento4 mp4decrypt with extracted keys"""
        if output_path is None:
            base_name = os.path.splitext(encrypted_file_path)[0]
            output_path = f"{base_name}_decrypted.m4a"
        
        # Format KID and key for mp4decrypt
        # mp4decrypt expects hex format: --key <kid>:<key>
        kid_hex = kid.replace('-', '').lower()
        
        mp4decrypt_path = os.path.join(os.getcwd(), 'bento4_tools', 'mp4decrypt')
        
        command = [
            mp4decrypt_path,
            '--show-progress',
            '--key', f'{kid_hex}:{key}',
            encrypted_file_path,
            output_path
        ]
        
        try:
            self.logger.info(f"Decrypting {encrypted_file_path} with mp4decrypt")
            self.logger.info(f"Using KID: {kid_hex}")
            self.logger.info(f"Output: {output_path}")
            
            result = subprocess.run(
                command,
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully decrypted to: {output_path}")
                self.logger.info(f"mp4decrypt output: {result.stdout}")
                return output_path
            else:
                self.logger.error(f"mp4decrypt failed: {result.stderr}")
                self.logger.error(f"Command output: {result.stdout}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error("mp4decrypt operation timed out")
            return None
        except Exception as e:
            self.logger.error(f"Error running mp4decrypt: {e}")
            return None

    def extract_media_info_from_audiobook(self, audiobook_data):
        """Extract media key, patron ID, and circulation ID from audiobook data"""
        try:
            title_data = audiobook_data['data']['title']
            
            # Extract media key
            media_key = title_data.get('mediaKey')
            
            # Extract circulation info
            circulation = title_data.get('circulation')
            if circulation:
                circulation_id = circulation.get('id')
                patron_id = circulation.get('patron', {}).get('id')
            else:
                circulation_id = None
                patron_id = None
                
            return {
                'media_key': media_key,
                'patron_id': patron_id,
                'circulation_id': circulation_id
            }
        except (KeyError, TypeError) as e:
            self.logger.error(f"Failed to extract media info: {e}")
            return None

    def get_audiobook_license(self, audiobook_data):
        """Get license blob for an audiobook using data from get_audiobook_details"""
        media_info = self.extract_media_info_from_audiobook(audiobook_data)
        
        if not media_info or not all(media_info.values()):
            self.logger.error("Missing required media information (media_key, patron_id, or circulation_id)")
            return None
            
        return self.get_license_blob(
            media_info['media_key'],
            media_info['patron_id'], 
            media_info['circulation_id']
        )

    def archive_audiobook_with_license(self, item_id):
        """Archive audiobook details and license blob"""
        self.logger.info(f"Archiving audiobook with license for ID: {item_id}")
        
        # Get audiobook details first
        audiobook_data = self.get_audiobook_details(item_id)
        if not audiobook_data:
            return None
            
        # Get license blob
        license_data = self.get_audiobook_license(audiobook_data)
        
        # Get MPD manifest
        media_info = self.extract_media_info_from_audiobook(audiobook_data)
        mpd_data = None
        if media_info and media_info['media_key']:
            mpd_data = self.get_mpd_manifest(media_info['media_key'])
        
        # Save audiobook details, license, and MPD manifest
        audiobook_filename = f"audiobook_{item_id}.json"
        self.save_data(audiobook_data, audiobook_filename)
        
        if license_data:
            license_filename = f"license_{item_id}.json"
            self.save_data(license_data, license_filename)
            
        if mpd_data:
            mpd_filename = f"mpd_{item_id}.json"
            self.save_data(mpd_data, mpd_filename)
            
        # Log results
        try:
            title = audiobook_data['data']['title']['title']
            status_parts = [f"archived: {title}"]
            if license_data:
                status_parts.append("license ✓")
            if mpd_data:
                status_parts.append("MPD ✓")
            self.logger.info(f"Successfully {', '.join(status_parts)}")
        except (KeyError, TypeError):
            self.logger.info(f"Successfully archived audiobook ID: {item_id}")
            
        return {
            'audiobook_data': audiobook_data,
            'license_data': license_data,
            'mpd_data': mpd_data
        }

    def download_with_ytdlp(self, item_id, output_dir=None):
        """Download audiobook using yt-dlp with MPD manifest"""
        if output_dir is None:
            output_dir = os.path.join('archive', f'downloads_{item_id}')
        
        os.makedirs(output_dir, exist_ok=True)
        
        # First get all the necessary data
        audiobook_data = self.get_audiobook_details(item_id)
        if not audiobook_data:
            self.logger.error(f"Could not get audiobook data for ID: {item_id}")
            return False
            
        license_data = self.get_audiobook_license(audiobook_data)
        if not license_data:
            self.logger.error(f"Could not get license data for ID: {item_id}")
            return False
            
        media_info = self.extract_media_info_from_audiobook(audiobook_data)
        if not media_info or not media_info['media_key']:
            self.logger.error(f"Could not extract media key for ID: {item_id}")
            return False
            
        # Construct MPD URL
        mpd_url = f"https://dash.hoopladigital.com/{media_info['media_key']}/Manifest.mpd"
        
        # Set up yt-dlp command with proper headers and authentication
        yt_dlp_path = os.path.join(os.getcwd(), 'venv', 'bin', 'yt-dlp')
        
        command = [
            yt_dlp_path,
            '--allow-unplayable-formats',  # Allow DRM-protected formats (developer option)
            '--allow-dynamic-mpd',  # Process dynamic DASH manifests
            '--concurrent-fragments', '4',  # Download multiple fragments simultaneously
            '--add-header', 'Referer:https://www.hoopladigital.com/',
            '--add-header', 'User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            '--add-header', f'Authorization:Bearer {self.token}',
            '--output', os.path.join(output_dir, f'audiobook_{item_id}_%(title)s.%(ext)s'),
            '--write-info-json',  # Save metadata
            '--write-description',  # Save description
            '--no-flat-playlist',  # Fully extract the videos of a playlist
            '--verbose',  # More detailed output for debugging
            mpd_url
        ]
        
        try:
            self.logger.info(f"Starting yt-dlp download for audiobook ID: {item_id}")
            self.logger.info(f"MPD URL: {mpd_url}")
            self.logger.info(f"Output directory: {output_dir}")
            
            # Run yt-dlp command
            result = subprocess.run(
                command, 
                cwd=os.getcwd(),
                capture_output=True, 
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully downloaded audiobook ID: {item_id}")
                self.logger.info(f"yt-dlp output: {result.stdout}")
                return True
            else:
                self.logger.error(f"yt-dlp failed for audiobook ID: {item_id}")
                self.logger.error(f"Error output: {result.stderr}")
                self.logger.error(f"Command output: {result.stdout}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"yt-dlp download timed out for audiobook ID: {item_id}")
            return False
        except Exception as e:
            self.logger.error(f"Error running yt-dlp for audiobook ID {item_id}: {e}")
            return False

    def archive_and_download_audiobook(self, item_id):
        """Complete workflow: archive metadata and download audiobook"""
        self.logger.info(f"Starting complete archive and download for ID: {item_id}")
        
        # First archive all metadata
        archive_result = self.archive_audiobook_with_license(item_id)
        if not archive_result:
            self.logger.error(f"Failed to archive metadata for ID: {item_id}")
            return False
            
        # Then download the audiobook
        download_result = self.download_with_ytdlp(item_id)
        
        return {
            'archive_success': bool(archive_result),
            'download_success': download_result,
            'archive_data': archive_result
        }

    def complete_audiobook_workflow(self, item_id):
        """Complete workflow: archive, download, extract DRM info, get license, and decrypt"""
        self.logger.info(f"Starting complete audiobook workflow for ID: {item_id}")
        
        # Step 1: Archive metadata (audiobook details, license, MPD)
        archive_result = self.archive_audiobook_with_license(item_id)
        if not archive_result:
            return {'success': False, 'error': 'Failed to archive metadata'}
        
        # Step 2: Download encrypted content using yt-dlp
        download_result = self.download_with_ytdlp(item_id)
        if not download_result:
            return {'success': False, 'error': 'Failed to download content'}
        
        # Step 3: Parse MPD manifest for DRM info
        mpd_data = archive_result.get('mpd_data')
        if not mpd_data:
            return {'success': False, 'error': 'No MPD data available'}
            
        drm_info = self.parse_mpd_manifest(mpd_data['mpd_content'])
        if not drm_info:
            return {'success': False, 'error': 'Failed to parse MPD manifest'}
        
        # Save DRM info
        drm_filename = f"drm_info_{item_id}.json"
        self.save_data(drm_info, drm_filename)
        
        # Step 4: Get Widevine license (if needed and PSSH available)
        license_data = archive_result.get('license_data')
        media_info = self.extract_media_info_from_audiobook(archive_result['audiobook_data'])
        
        widevine_license = None
        if drm_info.get('pssh_data', {}).get('widevine') and license_data:
            widevine_license = self.get_widevine_license(
                license_data['jwt_token'],
                drm_info['pssh_data'],
                media_info['patron_id'],
                media_info['circulation_id']
            )
            
            if widevine_license:
                widevine_filename = f"widevine_license_{item_id}.json"
                self.save_data(widevine_license, widevine_filename)
        
        # Step 5: Attempt decryption with mp4decrypt
        download_dir = os.path.join('archive', f'downloads_{item_id}')
        encrypted_files = [f for f in os.listdir(download_dir) if f.endswith('.m4a')]
        
        decryption_results = []
        if encrypted_files and drm_info.get('default_kid'):
            for encrypted_file in encrypted_files:
                encrypted_path = os.path.join(download_dir, encrypted_file)
                
                # For now, we'll try with a placeholder key since we need the actual 
                # Widevine CDM to extract the real keys
                # In a real implementation, this would come from the Widevine license response
                placeholder_key = "00" * 16  # 128-bit key of all zeros
                
                self.logger.warning("Using placeholder key - real implementation would extract from Widevine license")
                
                decrypted_path = self.decrypt_with_mp4decrypt(
                    encrypted_path,
                    drm_info['default_kid'],
                    placeholder_key,
                    os.path.join(download_dir, f"decrypted_{encrypted_file}")
                )
                
                decryption_results.append({
                    'input_file': encrypted_file,
                    'output_file': decrypted_path,
                    'success': decrypted_path is not None
                })
        
        # Step 6: Return comprehensive results
        result = {
            'success': True,
            'item_id': item_id,
            'archive_data': archive_result,
            'drm_info': drm_info,
            'widevine_license': widevine_license,
            'decryption_results': decryption_results,
            'workflow_stages': {
                'metadata_archive': bool(archive_result),
                'content_download': download_result,
                'drm_parsing': bool(drm_info),
                'license_acquisition': bool(widevine_license),
                'decryption_attempted': len(decryption_results) > 0
            }
        }
        
        self.logger.info("Complete audiobook workflow finished")
        self.logger.info(f"Workflow stages: {result['workflow_stages']}")
        
        return result

    def save_data(self, data, filename):
        """Save data to JSON file"""
        os.makedirs('archive', exist_ok=True)
        filepath = os.path.join('archive', filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Data saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save data to {filepath}: {e}")

    def archive_account_data(self):
        """Main method to archive account data"""
        if not self.login():
            self.logger.error("Authentication failed. Cannot proceed.")
            return False
        
        # Archive user info
        user_info = self.get_user_info()
        if user_info:
            self.save_data(user_info, 'user_info.json')
        
        # Archive borrowed items
        borrowed_items = self.get_borrowed_items()
        if borrowed_items:
            self.save_data(borrowed_items, 'borrowed_items.json')
        
        self.logger.info("Archive process completed")
        return True

if __name__ == "__main__":
    scraper = HooplaScraper()
    scraper.archive_account_data()