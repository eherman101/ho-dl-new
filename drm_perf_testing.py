#!/usr/bin/env python3
"""
DRM Performance Testing Suite with Browser Automation
For testing legitimate DRM implementations on owned content
Requires proper authorization and content ownership
"""

import time
import json
import base64
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from statistics import mean, median, stdev
from pathlib import Path
import subprocess

from playwright.async_api import async_playwright, Browser, Page
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DRMMetrics:
    """Store detailed DRM performance metrics"""
    auth_token_time: float
    manifest_parse_time: float
    license_request_time: float
    key_extraction_time: float
    first_segment_decrypt_time: float
    total_initialization_time: float
    playback_start_time: float
    buffer_health: Dict[str, float]
    network_metrics: Dict[str, float]
    cdm_operations: Dict[str, float]
    success: bool
    error: Optional[str] = None

class DRMPerformanceTester:
    """
    Test DRM performance using real browser CDM operations
    For authorized testing on owned content only
    """
    
    def __init__(self, config: Dict):
        """
        Initialize tester with configuration
        
        Args:
            config: Configuration including auth tokens and content IDs
        """
        self.config = config
        self.metrics_log = []
        
    async def setup_playwright_browser(self) -> Browser:
        """
        Setup Playwright browser with DRM support and performance monitoring
        """
        playwright = await async_playwright().start()
        
        # Launch Chromium with Widevine support
        browser = await playwright.chromium.launch(
            headless=False,  # DRM requires headed mode
            args=[
                '--enable-features=WidevineHardwareSecureDecryption',
                '--enable-logging=stderr',
                '--v=1',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )
        
        return browser
    
    def setup_selenium_browser(self) -> webdriver.Chrome:
        """
        Setup Selenium browser with performance logging for DRM testing
        """
        options = Options()
        options.add_argument('--enable-features=WidevineHardwareSecureDecryption')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Enable performance logging
        options.set_capability('goog:loggingPrefs', {
            'browser': 'ALL',
            'performance': 'ALL'
        })
        
        # Add CDP support for network monitoring
        options.add_experimental_option('w3c', True)
        
        driver = webdriver.Chrome(options=options)
        
        # Enable CDP for detailed network monitoring
        driver.execute_cdp_cmd('Network.enable', {})
        driver.execute_cdp_cmd('Performance.enable', {})
        
        return driver
    
    async def inject_performance_monitor(self, page: Page) -> None:
        """
        Inject JavaScript to monitor DRM and playback performance
        """
        monitoring_script = """
        window.drmMetrics = {
            licenseRequests: [],
            keyStatuses: [],
            decryptionTimes: [],
            bufferHealth: [],
            networkMetrics: []
        };
        
        // Monitor EME operations
        if (window.navigator.requestMediaKeySystemAccess) {
            const originalRequestAccess = window.navigator.requestMediaKeySystemAccess;
            window.navigator.requestMediaKeySystemAccess = async function(...args) {
                const startTime = performance.now();
                const result = await originalRequestAccess.apply(this, args);
                window.drmMetrics.keySystemAccessTime = performance.now() - startTime;
                return result;
            };
        }
        
        // Monitor license requests via Fetch API
        const originalFetch = window.fetch;
        window.fetch = async function(...args) {
            const url = args[0];
            const isLicenseRequest = url.includes('license') || url.includes('drm');
            
            if (isLicenseRequest) {
                const startTime = performance.now();
                const response = await originalFetch.apply(this, args);
                const duration = performance.now() - startTime;
                
                window.drmMetrics.licenseRequests.push({
                    url: url,
                    duration: duration,
                    timestamp: Date.now(),
                    status: response.status
                });
                
                return response;
            }
            
            return originalFetch.apply(this, args);
        };
        
        // Monitor video element for playback metrics
        function monitorVideoElement() {
            const video = document.querySelector('video');
            if (!video) {
                setTimeout(monitorVideoElement, 100);
                return;
            }
            
            // Track buffering
            video.addEventListener('waiting', () => {
                window.drmMetrics.bufferHealth.push({
                    event: 'buffering_start',
                    timestamp: Date.now(),
                    currentTime: video.currentTime
                });
            });
            
            video.addEventListener('playing', () => {
                window.drmMetrics.bufferHealth.push({
                    event: 'buffering_end',
                    timestamp: Date.now(),
                    currentTime: video.currentTime
                });
            });
            
            // Track first frame rendered
            video.addEventListener('loadeddata', () => {
                window.drmMetrics.firstFrameTime = performance.now();
            });
            
            // Monitor key status changes
            if (video.mediaKeys) {
                video.mediaKeys.addEventListener('keystatuseschange', (event) => {
                    const session = event.target;
                    const keyStatuses = [];
                    session.keyStatuses.forEach((status, keyId) => {
                        keyStatuses.push({
                            keyId: btoa(String.fromCharCode(...new Uint8Array(keyId))),
                            status: status,
                            timestamp: Date.now()
                        });
                    });
                    window.drmMetrics.keyStatuses.push(keyStatuses);
                });
            }
        }
        
        monitorVideoElement();
        
        // Performance observer for detailed metrics
        if (window.PerformanceObserver) {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.entryType === 'resource' && 
                        (entry.name.includes('.mp4') || entry.name.includes('.m4s') || 
                         entry.name.includes('.mpd') || entry.name.includes('manifest'))) {
                        window.drmMetrics.networkMetrics.push({
                            url: entry.name,
                            duration: entry.duration,
                            size: entry.transferSize,
                            timestamp: entry.startTime
                        });
                    }
                }
            });
            observer.observe({ entryTypes: ['resource'] });
        }
        """
        
        await page.evaluate(monitoring_script)
    
    async def test_drm_flow_playwright(self, url: str, auth_token: str) -> DRMMetrics:
        """
        Test complete DRM flow using Playwright
        """
        browser = await self.setup_playwright_browser()
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        # Setup request interception for auth
        await page.route('**/*', lambda route, request: self._handle_request(route, request, auth_token))
        
        # Inject performance monitoring
        await self.inject_performance_monitor(page)
        
        # Start timing
        start_time = time.perf_counter()
        
        # Navigate to content
        await page.goto(url)
        
        # Wait for video element and playback to start
        await page.wait_for_selector('video', timeout=30000)
        await page.wait_for_function('document.querySelector("video").readyState >= 2', timeout=30000)
        
        # Collect metrics
        metrics = await page.evaluate('window.drmMetrics')
        
        total_time = (time.perf_counter() - start_time) * 1000
        
        # Parse metrics into structured format
        drm_metrics = self._parse_browser_metrics(metrics, total_time)
        
        await browser.close()
        
        return drm_metrics
    
    def test_drm_flow_selenium(self, url: str, auth_token: str) -> DRMMetrics:
        """
        Test complete DRM flow using Selenium with CDP
        """
        driver = self.setup_selenium_browser()
        
        try:
            # Inject auth token into headers via CDP
            driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                'headers': {
                    'x-dt-auth-token': auth_token,
                    'Authorization': f'Bearer {self.config["bearer_token"]}'
                }
            })
            
            start_time = time.perf_counter()
            
            # Navigate to content
            driver.get(url)
            
            # Inject monitoring script
            with open('drm_monitor.js', 'r') as f:
                monitoring_script = f.read()
            driver.execute_script(monitoring_script)
            
            # Wait for video playback
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            wait = WebDriverWait(driver, 30)
            video = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'video')))
            
            # Wait for playback to start
            driver.execute_script("""
                return new Promise((resolve) => {
                    const video = document.querySelector('video');
                    if (video.readyState >= 2) resolve();
                    else video.addEventListener('loadeddata', resolve);
                });
            """)
            
            # Collect performance logs
            performance_logs = driver.get_log('performance')
            browser_logs = driver.get_log('browser')
            
            # Collect custom metrics
            metrics = driver.execute_script('return window.drmMetrics;')
            
            total_time = (time.perf_counter() - start_time) * 1000
            
            # Parse all metrics
            drm_metrics = self._parse_selenium_metrics(
                metrics, 
                performance_logs, 
                browser_logs, 
                total_time
            )
            
            return drm_metrics
            
        finally:
            driver.quit()
    
    def _parse_browser_metrics(self, metrics: Dict, total_time: float) -> DRMMetrics:
        """
        Parse browser-collected metrics into structured format
        """
        # Extract timing metrics
        license_times = [req['duration'] for req in metrics.get('licenseRequests', [])]
        network_times = [req['duration'] for req in metrics.get('networkMetrics', [])]
        
        # Calculate buffer health
        buffer_events = metrics.get('bufferHealth', [])
        rebuffer_count = sum(1 for e in buffer_events if e['event'] == 'buffering_start')
        
        return DRMMetrics(
            auth_token_time=metrics.get('keySystemAccessTime', 0),
            manifest_parse_time=next((m['duration'] for m in network_times 
                                     if 'manifest' in str(m.get('url', ''))), 0),
            license_request_time=mean(license_times) if license_times else 0,
            key_extraction_time=0,  # Would need CDM instrumentation
            first_segment_decrypt_time=metrics.get('firstFrameTime', 0),
            total_initialization_time=total_time,
            playback_start_time=metrics.get('firstFrameTime', 0),
            buffer_health={
                'rebuffer_count': rebuffer_count,
                'rebuffer_ratio': rebuffer_count / max(1, len(buffer_events))
            },
            network_metrics={
                'avg_segment_download': mean(network_times) if network_times else 0,
                'total_bytes': sum(m.get('size', 0) for m in metrics.get('networkMetrics', []))
            },
            cdm_operations={
                'key_sessions': len(metrics.get('keyStatuses', [])),
                'license_requests': len(license_times)
            },
            success=True,
            error=None
        )
    
    def _parse_selenium_metrics(self, custom_metrics: Dict, perf_logs: List, 
                               browser_logs: List, total_time: float) -> DRMMetrics:
        """
        Parse Selenium CDP metrics
        """
        # Parse performance logs
        network_events = []
        for log in perf_logs:
            message = json.loads(log['message'])
            method = message.get('message', {}).get('method', '')
            
            if method == 'Network.responseReceived':
                response = message['message']['params']['response']
                if any(x in response['url'] for x in ['license', 'manifest', '.mp4', '.m4s']):
                    network_events.append(response)
        
        # Similar parsing as Playwright
        return self._parse_browser_metrics(custom_metrics, total_time)
    
    async def run_concurrent_tests(self, url: str, num_concurrent: int = 5) -> List[DRMMetrics]:
        """
        Run concurrent DRM tests to measure scalability
        """
        tasks = []
        for i in range(num_concurrent):
            # Generate unique session for each test
            auth_token = self._get_auth_token(session_suffix=str(i))
            task = self.test_drm_flow_playwright(url, auth_token)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for r in results:
            if isinstance(r, DRMMetrics):
                valid_results.append(r)
            else:
                logger.error(f"Test failed: {r}")
        
        return valid_results
    
    def _get_auth_token(self, session_suffix: str = "") -> str:
        """
        Get auth token for testing (implement your token generation)
        """
        # This would call your actual auth endpoint
        # For testing, return a mock token
        return f"test_token_{session_suffix}"
    
    async def _handle_request(self, route, request, auth_token):
        """
        Intercept and modify requests for auth injection
        """
        headers = {
            **request.headers,
            'x-dt-auth-token': auth_token,
        }
        await route.continue_(headers=headers)

def analyze_drm_metrics(metrics_list: List[DRMMetrics]) -> None:
    """
    Analyze and report DRM performance metrics
    """
    if not metrics_list:
        print("No metrics to analyze")
        return
    
    successful = [m for m in metrics_list if m.success]
    failed = [m for m in metrics_list if not m.success]
    
    print("\n" + "="*80)
    print("DRM PERFORMANCE TEST RESULTS")
    print("="*80)
    print(f"Total Tests: {len(metrics_list)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        # Aggregate metrics
        metrics_dict = {
            'License Request Time (ms)': [m.license_request_time for m in successful],
            'Manifest Parse Time (ms)': [m.manifest_parse_time for m in successful],
            'First Frame Time (ms)': [m.playback_start_time for m in successful],
            'Total Init Time (ms)': [m.total_initialization_time for m in successful],
            'Rebuffer Count': [m.buffer_health.get('rebuffer_count', 0) for m in successful],
        }
        
        print("\n" + "-"*40)
        print("Performance Metrics Summary:")
        print("-"*40)
        
        for metric_name, values in metrics_dict.items():
            if values and any(v > 0 for v in values):
                print(f"\n{metric_name}:")
                print(f"  Mean: {mean(values):.2f}")
                print(f"  Median: {median(values):.2f}")
                if len(values) > 1:
                    print(f"  StdDev: {stdev(values):.2f}")
                print(f"  Min: {min(values):.2f}")
                print(f"  Max: {max(values):.2f}")
        
        # Network metrics
        total_bytes = sum(m.network_metrics.get('total_bytes', 0) for m in successful)
        avg_segment_time = mean([m.network_metrics.get('avg_segment_download', 0) 
                                for m in successful if m.network_metrics.get('avg_segment_download', 0) > 0])
        
        print(f"\nNetwork Performance:")
        print(f"  Total Data Transferred: {total_bytes / (1024*1024):.2f} MB")
        print(f"  Avg Segment Download Time: {avg_segment_time:.2f} ms")
        
        # CDM operations
        total_licenses = sum(m.cdm_operations.get('license_requests', 0) for m in successful)
        print(f"\nDRM Operations:")
        print(f"  Total License Requests: {total_licenses}")
        print(f"  Avg License Requests per Session: {total_licenses/len(successful):.2f}")

async def main():
    """
    Main test execution
    """
    config = {
        'bearer_token': 'your_bearer_token',
        'content_url': 'https://www.hoopladigital.com/play/your_content_id',
        'user_id': '13914483',
        'session_id': '423234040'
    }
    
    tester = DRMPerformanceTester(config)
    
    # Single test with Playwright
    print("Running single DRM flow test with Playwright...")
    metric = await tester.test_drm_flow_playwright(
        config['content_url'],
        tester._get_auth_token()
    )
    analyze_drm_metrics([metric])
    
    # Concurrent tests
    print("\nRunning concurrent DRM tests...")
    concurrent_metrics = await tester.run_concurrent_tests(
        config['content_url'],
        num_concurrent=3
    )
    analyze_drm_metrics(concurrent_metrics)
    
    # Selenium test for comparison
    print("\nRunning Selenium DRM test...")
    selenium_metric = tester.test_drm_flow_selenium(
        config['content_url'],
        tester._get_auth_token()
    )
    analyze_drm_metrics([selenium_metric])

if __name__ == "__main__":
    asyncio.run(main())
