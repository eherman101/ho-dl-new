#!/usr/bin/env python3
"""
Hoopla Digital Archive Scraper
Educational and research purposes only
"""

import os
import requests
import json
from urllib.parse import quote
from dotenv import load_dotenv
import logging

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