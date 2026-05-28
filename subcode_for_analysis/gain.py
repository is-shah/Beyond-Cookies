from import_lib import *

import requests
import json
import os

def download_disconnect_list():
    """
    Download the Disconnect.me tracker protection list
    """
    # URL for the Disconnect.me services list
    url = "https://raw.githubusercontent.com/disconnectme/disconnect-tracking-protection/master/services.json"

    print("Downloading Disconnect.me tracker list...")
    print(f"URL: {url}")

    try:
        # Download the file
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse JSON
        json_data = response.json()

        # Create directory if it doesn't exist
        os.makedirs('dataset_disconnect', exist_ok=True)

        # Save to file
        output_file = 'dataset_disconnect/services-relay-disconnect.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Successfully downloaded and saved to: {output_file}")

        # Display available categories
        if 'categories' in json_data:
            print("\nAvailable categories:")
            for category in json_data['categories'].keys():
                domain_count = len(json_data['categories'][category])
                print(f"  - {category}: {domain_count} domains")

        return json_data

    except requests.exceptions.RequestException as e:
        print(f"✗ Error downloading file: {e}")
        print("\nAlternative URLs to try:")
        print("1. https://raw.githubusercontent.com/disconnectme/disconnect-tracking-protection/master/services.json")
        print("2. https://services.disconnect.me/disconnect-plaintext.json")
        return None
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing JSON: {e}")
        return None

def extract_domains_from_category(category_list):
    """
    Extract all domains from a nested category structure

    Format:
    [
      {"ServiceName": {"url": ["domain1", "domain2"]}},
      ...
    ]
    """
    domains = set()

    for item in category_list:
        # Each item is a dict with one key (service name)
        for service_name, service_data in item.items():
            # service_data is a dict with URLs as keys and domain lists as values
            for url, domain_list in service_data.items():
                # Add all domains from the list
                domains.update(domain_list)

    return domains

def load_and_process_disconnect_data(json_file='dataset_disconnect/services-relay-disconnect.json'):
    """
    Load the Disconnect.me list and extract fingerprinting domains
    """
    print(f"\nLoading Disconnect.me data from: {json_file}")

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        # Extract domains from FingerprintingInvasive and FingerprintingGeneral categories
        fp_invasive_list = json_data.get("categories", {}).get("FingerprintingInvasive", [])
        fp_general_list = json_data.get("categories", {}).get("FingerprintingGeneral", [])

        # Parse the nested structure to extract actual domains
        fp_invasive_domains = extract_domains_from_category(fp_invasive_list)
        fp_general_domains = extract_domains_from_category(fp_general_list)


        print(f"✓ Loaded successfully")
        print(f"  - FingerprintingInvasive domains: {len(fp_invasive_domains)}")
        print(f"  - FingerprintingGeneral domains: {len(fp_general_domains)}")


        # Display some example domains
        if fp_invasive_domains:
            print(f"\nExample FingerprintingInvasive domains:")
            for domain in list(fp_invasive_domains)[:5]:
                print(f"  - {domain}")

        if fp_general_domains:
            print(f"\nExample FingerprintingGeneral domains:")
            for domain in list(fp_general_domains)[:5]:
                print(f"  - {domain}")

        return fp_invasive_domains, fp_general_domains

    except FileNotFoundError:
        print(f"✗ File not found: {json_file}")
        print("Run download_disconnect_list() first to download the file.")
        return None, None, None, None
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing JSON: {e}")
        return None, None, None, None

def apply_disconnect_categories_to_dataframe(df, domain_column='domain_script_url'):
    """
    Apply FingerprintingInvasive and FingerprintingGeneral boolean columns to dataframe

    Parameters:
    - df: pandas DataFrame with script/request data
    - domain_column: column name containing the domain to check
    """
    # Load the disconnect data
    fp_invasive_domains, fp_general_domains = load_and_process_disconnect_data()

    if fp_invasive_domains is None:
        print("Failed to load Disconnect.me data. Attempting to download...")
        json_data = download_disconnect_list()
        if json_data:
            fp_invasive_list = json_data.get("categories", {}).get("FingerprintingInvasive", [])
            fp_general_list = json_data.get("categories", {}).get("FingerprintingGeneral", [])


            fp_invasive_domains = extract_domains_from_category(fp_invasive_list)
            fp_general_domains = extract_domains_from_category(fp_general_list)

        else:
            return df

    # Create boolean columns
    print(f"\nApplying categories to dataframe...")
    df['FingerprintingInvasive'] = df[domain_column].isin(fp_invasive_domains)
    df['FingerprintingGeneral'] = df[domain_column].isin(fp_general_domains)


    print(f"✓ Categories applied:")
    print(f"  - FingerprintingInvasive: {df['FingerprintingInvasive'].sum()} matches")
    print(f"  - FingerprintingGeneral: {df['FingerprintingGeneral'].sum()} matches")


    return df

# ============================================================
# MAIN EXECUTION
# ============================================================

df_baseline = pd.read_csv("safe_baseline/js.csv")
df_modified = pd.read_csv("REJECT/js.csv")
common_domains_df = pd.read_csv('common_domains.csv')

json_data = download_disconnect_list()

if json_data:
    # Step 2: Load and process
    df_javascript_baseline = apply_disconnect_categories_to_dataframe(
        df_baseline,
        domain_column='domain_script_url'
    )
    df_javascript_modified = apply_disconnect_categories_to_dataframe(
        df_modified,
        domain_column='domain_script_url'
    )

# Filter only common domains
df_javascript_baseline = df_javascript_baseline[
    df_javascript_baseline["domain"].isin(common_domains_df["domains"])
]

# df_javascript_modified = df_javascript_modified[
#     df_javascript_modified["domain"].isin(common_domains_df["domains"])
# ]

df_javascript_baseline_accept = df_javascript_baseline[df_javascript_baseline['clicked_stage'].isin([
    'Before Interaction (Accept)',
    'After Interaction (Accept)',
])]

df_javascript_modified_accept = df_javascript_modified[df_javascript_modified['clicked_stage'].isin([
    # 'Before Interaction (Reject)',
    'After Interaction (Reject)',
])]

import json

json_file_path = 'dataset_disconnect/services-relay-disconnect.json'
with open(json_file_path, 'r') as f:
    json_data = json.load(f)

# Step 2: Desired categories
selected_categories = [
    "Email",
    "EmailAggressive",
    "Advertising",
    "Analytics",
    "FingerprintingInvasive",
    "FingerprintingGeneral",
    "Anti-fraud",
    "Social",
    "Cryptomining"
]

# Step 3: Collect all third-party domains
disconnect_domains = set()

categories = json_data.get("categories", {})

for category_name, services_list in categories.items():
    if category_name not in selected_categories:
        continue
    for service_item in services_list:

        for service_name, url_map in service_item.items():

            for url, domains in url_map.items():

                disconnect_domains.update(domains)
                #Internal domains at last depth

print(f"Total domains collected: {len(disconnect_domains)}")
# print(disconnect_domains)

df_javascript_baseline_accept = df_javascript_baseline_accept[
    (df_javascript_baseline_accept['AllList'] == True) &
    ((df_javascript_baseline_accept['FingerprintingInvasive'] == True) | (df_javascript_baseline_accept['FingerprintingGeneral'] == True)) &
    (df_javascript_baseline_accept['domain_script_url'] != df_javascript_baseline_accept['domain']) 
]

df_javascript_modified_accept = df_javascript_modified_accept[
    (df_javascript_modified_accept['AllList'] == True) &
    ((df_javascript_modified_accept['FingerprintingInvasive'] == True) | (df_javascript_modified_accept['FingerprintingGeneral'] == True)) &
    (df_javascript_modified_accept['domain_script_url'] != df_javascript_modified_accept['domain']) 
]


# print(f"Unique domains for baseline : {df_javascript_baseline_accept['domain'].nunique()}")
# print(f"Unique domains for modified : {df_javascript_modified_accept['domain'].nunique()}")

# print(f"Number of rows: {df_javascript_baseline_accept.shape[0]}")
# print(f"Number of rows: {df_javascript_modified_accept.shape[0]}")


# Step 1: unique symbol count per domain
# domain_symbol_counts_baseline = (
#     df_javascript_baseline_accept
#     .groupby('domain')['symbol']
#     .nunique()
# )

# Step 2: median across domains
# median_unique_fingerprint_count_baseline = domain_symbol_counts_baseline.median()

# print(f"Median unique fingerprint symbols per domain - baseline : {median_unique_fingerprint_count_baseline}")


# # Step 1: unique symbol count per domain
# domain_symbol_counts_modified = (
#     df_javascript_modified_accept
#     .groupby('domain')['symbol']
#     .nunique()
# )

# # Step 2: median across domains
# median_unique_fingerprint_count_modified = domain_symbol_counts_modified.median()

# print(f"Median unique fingerprint symbols per domain - modified : {median_unique_fingerprint_count_modified}")


#-----------------------------------------------------------------------------------------------
browser_info_symbols = [
    "Navigator.userAgent",
    "Navigator.language",
    "Navigator.platform",
    "Navigator.maxTouchPoints",
    "Navigator.plugins",
    "Navigator.javaEnabled",
    "Navigator.toString",
    "Navigator.hardwareConcurrency",
    "Navigator.webdriver",
    "Navigator.oscpu",
    "Navigator.appVersion",
    "Navigator.cookieEnabled",
    "Navigator.appCodeName",
    "Navigator.appName",
    "Navigator.product",
    "Navigator.doNotTrack",
    "Navigator.globalPrivacyControl",
    "Navigator.buildID",
    "Navigator.productSub",
    "Navigator.credentials",
    "Navigator.vendor",
    "Navigator.wakeLock",
    "Navigator.hasOwnProperty",
    "Navigator.mimeTypes",
    "Navigator.sendBeacon",
    "Navigator.permissions",
    "Navigator.getGamepads",
    "Navigator.languages",
    "Navigator.serviceWorker",
    "Navigator.geolocation",
    "Navigator.onLine",
    "Navigator.userActivation",
    "Navigator.pdfViewerEnabled",
    "Navigator.mediaCapabilities",
    "Navigator.vendorSub",
    "Navigator.mediaDevices",
    "Navigator.clipboard",
    "Navigator.mediaSession",
    "Navigator.locks",
    "Navigator.storage",
    "Navigator.requestMediaKeySystemAccess",
    "Navigator.__proto__"
]

# =============================================================================
# SCREEN & DISPLAY INFORMATION
# =============================================================================
# Detects screen-based fingerprinting
# Used for: Screen resolution, color depth, orientation tracking
screen_display_info_symbols = [
    'window.screen.width',
    'window.screen.height',
    'window.screen.availWidth',
    'window.screen.availHeight',
    'window.screen.availTop',
    'window.screen.availLeft',
    'window.screen.colorDepth',
    'window.screen.pixelDepth',
    'window.screen.orientation',  # Screen orientation API
    'window.devicePixelRatio',  # Pixel density
    'window.innerWidth',  # Viewport dimensions
    'window.innerHeight',
    'window.outerWidth',  # Browser window dimensions
    'window.outerHeight',
    'window.screenX',  # Window position
    'window.screenY',
    'window.screenLeft',
    'window.screenTop',
    'window.matchMedia',
    'MediaQueryList.matches',
    'window.screen',
    'BarProp.visible',
]

# =============================================================================
# STORAGE APIs
# =============================================================================
# Detects stateful tracking through browser storage mechanisms
# Used for: Cookie tracking, persistent storage, storage fingerprinting
# storage_info_symbols = [
#     # Local Storage
#     'window.localStorage',
#     'window.sessionStorage',
#     'Storage.getItem',
#     'Storage.setItem',
#     'Storage.removeItem',
#     'Storage.clear',
#     'Storage.length',
#     'Storage.key',
#     'Storage.toString',
#     'Storage.hasOwnProperty',
#     'Navigator.cookieEnabled',
#     'Navigator.storage',
#     'window.indexedDB',
#     'window.openDatabase', 
#     'window.document.referrer',
#     'window.document.cookie',
#     'window.name',
#     'Document.cookie'  # Web SQL (deprecated but still used)
# ]


# # =============================================================================
# # HTML CANVAS FINGERPRINTING
# # =============================================================================
# # Detects Canvas-based fingerprinting (one of most common techniques)
# # Used for: Graphics card fingerprinting, font rendering differences
# html_canvas_info_symbols = [
#     # Canvas Element Properties
#     'HTMLCanvasElement.getContext',
#     'HTMLCanvasElement.width',
#     'HTMLCanvasElement.height',
#     'HTMLCanvasElement.toDataURL',  # Image data extraction
#     'HTMLCanvasElement.toBlob',  # Binary data extraction
#     'HTMLCanvasElement.addEventListener',
#     'HTMLCanvasElement.tagName',
#     'HTMLCanvasElement.setAttribute',
#     'HTMLCanvasElement.style',
#     'HTMLCanvasElement.toString',
#     'HTMLCanvasElement.children',

#     # Canvas 2D Rendering Context - Drawing Operations
#     'CanvasRenderingContext2D.fillRect',
#     'CanvasRenderingContext2D.strokeRect',
#     'CanvasRenderingContext2D.clearRect',
#     'CanvasRenderingContext2D.fill',
#     'CanvasRenderingContext2D.stroke',
#     'CanvasRenderingContext2D.rect',
#     'CanvasRenderingContext2D.arc',
#     'CanvasRenderingContext2D.ellipse',
#     'CanvasRenderingContext2D.bezierCurveTo',

#     # Canvas 2D Rendering Context - Text Operations (HIGH FINGERPRINTING VALUE)
#     'CanvasRenderingContext2D.fillText',
#     'CanvasRenderingContext2D.strokeText',
#     'CanvasRenderingContext2D.measureText',  # Font rendering measurement
#     'CanvasRenderingContext2D.font',
#     'CanvasRenderingContext2D.textAlign',
#     'CanvasRenderingContext2D.textBaseline',

#     # Canvas 2D Rendering Context - Image Data (CRITICAL FOR FINGERPRINTING)
#     'CanvasRenderingContext2D.getImageData',  # Pixel data extraction
#     'CanvasRenderingContext2D.putImageData',
#     'CanvasRenderingContext2D.createImageData',

#     # Canvas 2D Rendering Context - Styles & Effects
#     'CanvasRenderingContext2D.fillStyle',
#     'CanvasRenderingContext2D.strokeStyle',
#     'CanvasRenderingContext2D.shadowColor',
#     'CanvasRenderingContext2D.shadowBlur',
#     'CanvasRenderingContext2D.shadowOffsetX',
#     'CanvasRenderingContext2D.shadowOffsetY',
#     'CanvasRenderingContext2D.lineWidth',
#     'CanvasRenderingContext2D.lineCap',
#     'CanvasRenderingContext2D.lineJoin',
#     'CanvasRenderingContext2D.lineDashOffset',
#     'CanvasRenderingContext2D.setLineDash',
#     'CanvasRenderingContext2D.miterLimit',
#     'CanvasRenderingContext2D.filter',
#     'CanvasRenderingContext2D.globalCompositeOperation',
#     'CanvasRenderingContext2D.globalAlpha',
#     'CanvasRenderingContext2D.imageSmoothingEnabled',

#     # Canvas 2D Rendering Context - Transformations
#     'CanvasRenderingContext2D.rotate',
#     'CanvasRenderingContext2D.scale',
#     'CanvasRenderingContext2D.translate',
#     'CanvasRenderingContext2D.transform',
#     'CanvasRenderingContext2D.setTransform',
#     'CanvasRenderingContext2D.resetTransform',

#     # Canvas 2D Rendering Context - Gradients & Patterns
#     'CanvasRenderingContext2D.createLinearGradient',
#     'CanvasRenderingContext2D.createRadialGradient',
#     'CanvasRenderingContext2D.createPattern',

#     # Canvas 2D Rendering Context - State Management
#     'CanvasRenderingContext2D.save',
#     'CanvasRenderingContext2D.restore',

#     # Canvas 2D Rendering Context - Path Operations
#     'CanvasRenderingContext2D.isPointInPath',  # Path detection
#     'CanvasRenderingContext2D.isPointInStroke',

#     # Canvas 2D Rendering Context - Other
#     'CanvasRenderingContext2D.hasOwnProperty',
#     'CanvasRenderingContext2D.canvas'
# ]

# =============================================================================
# WEBGL FINGERPRINTING
# =============================================================================
# Detects WebGL-based fingerprinting (graphics card identification)
# Used for: GPU fingerprinting, driver detection, rendering capabilities
webgl_info_symbols = [
    # WebGL Context
    'WebGLRenderingContext.getParameter',  # GPU parameters
    'WebGLRenderingContext.getExtension',  # Extension enumeration
    'WebGLRenderingContext.getSupportedExtensions',  # Available extensions
    'WebGLRenderingContext.getShaderPrecisionFormat',  # Shader precision
    'WebGLRenderingContext.getContextAttributes',  # Context configuration
    'WebGLRenderingContext.readPixels',  # Pixel data extraction
    'WebGLRenderingContext.canvas',

    # WebGL2 Context (newer API)
    'WebGL2RenderingContext.getParameter',
    'WebGL2RenderingContext.getExtension',
    'WebGL2RenderingContext.getSupportedExtensions',
    'WebGL2RenderingContext.getShaderPrecisionFormat',
    'WebGL2RenderingContext.getContextAttributes',
    'WebGL2RenderingContext.readPixels',
    'WebGL2RenderingContext.canvas'
]

# =============================================================================
# WEBRTC (IP LEAKAGE & FINGERPRINTING)
# =============================================================================
# Detects WebRTC usage for IP address leakage and connection fingerprinting
# Used for: Real IP detection (bypassing VPN), connection fingerprinting
webrtc_info_symbols = [
    'RTCPeerConnection.createDataChannel',
    'RTCPeerConnection.createOffer',
    'RTCPeerConnection.createAnswer',
    'RTCPeerConnection.setLocalDescription',
    'RTCPeerConnection.setRemoteDescription',
    'RTCPeerConnection.addIceCandidate',  # ICE candidate harvesting
    'RTCPeerConnection.onicecandidate',  # IP address extraction
    'RTCPeerConnection.iceGatheringState',
    'RTCPeerConnection.iceConnectionState',
    'RTCPeerConnection.connectionState',
    'RTCPeerConnection.addEventListener',
    'RTCPeerConnection.removeEventListener',
    'RTCPeerConnection.close',
    'RTCPeerConnection.getStats',  # Connection statistics
    'RTCPeerConnection.toString',
    'RTCPeerConnectionIceEvent'  # ICE event handling
]

# =============================================================================
# AUDIO FINGERPRINTING
# =============================================================================
# Detects audio-based fingerprinting (audio hardware characteristics)
# Used for: Audio stack fingerprinting, hardware/driver detection
audio_fingerprinting_symbols = [
    # Audio Contexts
    'AudioContext',
    'AudioContext.createOscillator',
    'AudioContext.createAnalyser',
    'AudioContext.createGain',
    'AudioContext.createScriptProcessor',
    'AudioContext.createDynamicsCompressor',
    'AudioContext.createBiquadFilter',
    'AudioContext.destination',
    'AudioContext.sampleRate',
    'AudioContext.currentTime',
    'AudioContext.state',
    'AudioContext.listener',
    'AudioContext.resume',
    # Offline Audio Context (commonly used for fingerprinting)
    'OfflineAudioContext',
    'OfflineAudioContext.createOscillator',
    'OfflineAudioContext.createAnalyser',
    'OfflineAudioContext.createDynamicsCompressor',
    'OfflineAudioContext.createBiquadFilter',
    'OfflineAudioContext.createScriptProcessor',
    'OfflineAudioContext.destination',
    'OfflineAudioContext.startRendering',  # Audio rendering
    'OfflineAudioContext.oncomplete',
    'OfflineAudioContext.state',
    'OfflineAudioContext.listener',
    'OfflineAudioContext.addEventListener',

    # Audio Nodes
    'OscillatorNode',
    'OscillatorNode.type',
    'OscillatorNode.frequency',
    'OscillatorNode.detune',
    'OscillatorNode.start',
    'OscillatorNode.stop',
    'OscillatorNode.connect',
    'OscillatorNode.disconnect',

    'GainNode',
    'GainNode.gain',
    'GainNode.connect',

    'ScriptProcessorNode',
    'ScriptProcessorNode.onaudioprocess',

    'AnalyserNode',
    'AnalyserNode.fftSize',
    'AnalyserNode.frequencyBinCount',
    'AnalyserNode.minDecibels',
    'AnalyserNode.maxDecibels',
    'AnalyserNode.smoothingTimeConstant',
    'AnalyserNode.getFloatFrequencyData',  # Frequency analysis
    'AnalyserNode.getByteFrequencyData',
    'AnalyserNode.getFloatTimeDomainData',  # Time domain analysis
    'AnalyserNode.getByteTimeDomainData',
    'AnalyserNode.channelCount',
    'AnalyserNode.channelCountMode',
    'AnalyserNode.channelInterpretation',
    'AnalyserNode.context',
    'AnalyserNode.numberOfInputs',
    'AnalyserNode.numberOfOutputs',

    # AudioBuffer Fingerprinting
    'AudioBuffer',
    'AudioBuffer.length',
    'AudioBuffer.sampleRate',
    'AudioBuffer.duration',
    'AudioBuffer.numberOfChannels',
    'AudioBuffer.getChannelData',        # Float32Array output used for hash computation
    'AudioBuffer.copyFromChannel',
    'AudioBuffer.copyToChannel',

    # AudioWorkletNode Fingerprinting
    'AudioWorkletNode',
    'AudioWorkletNode.port',             # MessagePort for processor communication
    'AudioWorkletNode.parameters',       # AudioParamMap — parameter precision varies per engine
    'AudioWorkletNode.processorOptions',
    'AudioWorkletNode.channelCount',
    'AudioWorkletNode.channelCountMode',
    'AudioWorkletNode.channelInterpretation',
    'AudioWorkletNode.context',          # Links back to BaseAudioContext state
    'AudioWorkletNode.numberOfInputs',
    'AudioWorkletNode.numberOfOutputs',
]

# =============================================================================
# DEVICE SENSORS & MOTION
# =============================================================================
# Detects device sensor access (accelerometer, gyroscope)
# Used for: Device orientation fingerprinting, motion patterns
device_sensor_symbols = [
    # Device Motion (Accelerometer)
    'DeviceMotionEvent.acceleration',
    'DeviceMotionEvent.accelerationIncludingGravity',
    'DeviceMotionEvent.rotationRate',
    'DeviceMotionEvent.interval',
    'window.ondevicemotion',

    # Device Orientation (Gyroscope)
    'DeviceOrientationEvent.alpha',
    'DeviceOrientationEvent.beta',
    'DeviceOrientationEvent.gamma',
    'DeviceOrientationEvent.absolute',
    'window.ondeviceorientation',

]



# =============================================================================
# PERFORMANCE & TIMING APIs
# =============================================================================
# Detects timing-based fingerprinting and performance measurement
# Used for: Timing attacks, clock skew detection, performance profiling
performance_timing_symbols = [
    'window.performance',
    'Performance.now',
    'Performance.timing',
    'Performance.navigation',
    'Performance.getEntries',
    'Performance.measure',
    'Performance.mark',
    'Performance.setResourceTimingBufferSize',

    'PerformanceTiming.navigationStart',
    'PerformanceTiming.fetchStart',
    'PerformanceTiming.domComplete',
    'PerformanceTiming.loadEventEnd',

    # High Resolution Time
    'Date.getTime',
    'Date.getTimezoneOffset',  # Timezone fingerprinting
    'Date.now',

    # Animation Timing
    'Animation.currentTime',
    'Animation.startTime',
    'window.requestAnimationFrame',
    'Performance.getEntriesByType',
    'Performance.getEntriesByName',
    'Performance.clearMarks',
    'URL.createObjectURL',
    'URL.revokeObjectURL'

]

# =============================================================================
# FONT ENUMERATION
# =============================================================================
# Detects font-based fingerprinting
# Used for: Installed font detection, system identification
font_enumeration_symbols = [
    'window.document.fonts',
    'window.document.fonts.check',  # Font availability check
    'window.document.fonts.load',
    'window.document.fonts.ready',
    'FontFaceSet.check',
    'FontFaceSet.load'
]

# =============================================================================
# MEDIA DEVICES & CAPABILITIES
# =============================================================================
# Detects media device enumeration (cameras, microphones, speakers)
# Used for: Device fingerprinting, hardware identification
media_devices_symbols = [
    'MediaDevices.enumerateDevices',  # Device enumeration
    'MediaDevices.getUserMedia',
    'MediaDevices.getDisplayMedia',
    'MediaDevices.getSupportedConstraints',

    'HTMLMediaElement.canPlayType',  # Codec support detection
    'MediaSource.isTypeSupported',  # Media source support

    'speechSynthesis.getVoices',  # Speech synthesis voices
    'SpeechSynthesis.getVoices'
]

# =============================================================================
# ELEMENT & LAYOUT FINGERPRINTING
# =============================================================================
# Detects element measurement and layout-based fingerprinting
# Used for: Font rendering differences, layout engine fingerprinting
element_layout_symbols = [
    'Element.getClientRects',  # Element positioning
    'Element.getBoundingClientRect',
    'Element.offsetWidth',
    'Element.offsetHeight',
    'Element.clientWidth',
    'Element.clientHeight',
    'Element.scrollWidth',
    'Element.scrollHeight',
    'HTMLCanvasElement.offsetParent',

]

# =============================================================================
# KEYBOARD & INPUT FINGERPRINTING
# =============================================================================
# Detects keyboard layout and input characteristics
# Used for: Keyboard layout detection, typing pattern analysis
keyboard_input_symbols = [
    'KeyboardEvent.key',
    'KeyboardEvent.code',
    'KeyboardEvent.keyCode',
    'KeyboardEvent.charCode',
    'KeyboardEvent.which',
    'KeyboardEvent.location',
    'KeyboardEvent.timeStamp',  # Timing between keystrokes
    'Event.timeStamp'
]

# =============================================================================
# COMMUNICATION CHANNELS
# =============================================================================
# Detects cross-context communication mechanisms
# Used for: Cross-tab tracking, worker-based fingerprinting
communication_symbols = [
    'SharedWorker',
    'SharedWorker.constructor',
    'BroadcastChannel',
    'BroadcastChannel.constructor',
    'BroadcastChannel.postMessage',
    'MessageChannel',
    'Worker'
]

permission_preference_symbols = [
    'Notification.permission',
    'Notification.requestPermission'
]


# =============================================================================
# MISCELLANEOUS FINGERPRINTING VECTORS
# =============================================================================
# Other fingerprinting techniques and APIs

# =============================================================================
# SYMBOL CATEGORIES DICTIONARY
# =============================================================================
# Organized mapping of all fingerprinting categories
symbol_categories = {
    'Navigator-based Fingerprinting': browser_info_symbols,
    'Screen/Display Fingerprinting': screen_display_info_symbols,
    'Audio Fingerprinting': audio_fingerprinting_symbols,
    'Performance & Timing Fingerprinting': performance_timing_symbols,
    'Font Fingerprinting': font_enumeration_symbols,
    'Media I/O fingerprinting': media_devices_symbols,
    'DOM Layout Fingerprinting': element_layout_symbols,
    'keystroke Fingerprinting': keyboard_input_symbols,
    'Runtime State Fingerprinting': permission_preference_symbols,
    'WebRTC' : webrtc_info_symbols,
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_symbol_category(symbol):
    """
    Returns the category name for a given symbol.

    Args:
        symbol (str): JavaScript symbol/API to categorize

    Returns:
        str: Category name or 'Other' if not found
    """
    for category, symbol_list in symbol_categories.items():
        if symbol in symbol_list:
            return category

    print(f"Other symbol found: {symbol}")
    return "Other"


# Step 1: assign category
df_javascript_modified_accept['symbol_category'] = df_javascript_modified_accept['symbol'].map(get_symbol_category)

# # Step 2: filter only Audio Fingerprinting rows
# df_1 = df_javascript_modified_accept[
#     df_javascript_modified_accept['symbol_category'] == 'Screen/Display Fingerprinting'
# ]

# df_javascript_baseline_accept['symbol_category'] = df_javascript_baseline_accept['symbol'].map(get_symbol_category)

# # Step 2: filter only Audio Fingerprinting rows
# df_2 = df_javascript_baseline_accept[
#     df_javascript_baseline_accept['symbol_category'] == 'Screen/Display Fingerprinting'
# ]


other_symbols = (
df_javascript_modified_accept[df_javascript_modified_accept['symbol_category'] == 'Other']['symbol']
.unique()
)

print(f"Other Symbols - {other_symbols}")
# Count unique domains per category
category_site_counts = (
df_javascript_modified_accept
.groupby('symbol_category')['domain']
.nunique()
.reset_index(name='unique_site_count')
.sort_values(by='unique_site_count', ascending=False)
)

print(category_site_counts)

# Step 3: unique symbols per domain
# audio_domain_counts = (
#     df_media
#     .groupby('domain')['symbol']
#     .nunique()
# )

# # Step 4: median across domains
# median_audio_fingerprints_modified = audio_domain_counts.median()

# print(f"Median unique Audio Fingerprinting symbols per domain: {median_audio_fingerprints_modified}")





# # # Add a new column for symbol category
# # df_javascript_reject['symbol_category'] = df_javascript_reject['symbol'].map(get_symbol_category) 
# # ## what is much better to have - if we want to present the reviewers - popalatson idst

# # other_symbols = (
# # df_javascript_reject[df_javascript_reject['symbol_category'] == 'Other']['symbol']
# # .unique()
# # )

# # print(f"Other Symbols - {other_symbols}")
# # # Count unique domains per category
# # category_site_counts = (
# # df_javascript_reject
# # .groupby('symbol_category')['domain']
# # .nunique()
# # .reset_index(name='unique_site_count')
# # .sort_values(by='unique_site_count', ascending=False)
# # )

# # # Display the result
# # print(category_site_counts)
# #-------------------------------------------------------------------------------------------------
# filtered_df = df_javascript_reject
# tracking_to_domains = defaultdict(set)

# for _, row in filtered_df.iterrows():
#     tracking_to_domains[row['domain_script_url']].add(row['domain'])

# # Step 7: Count how many unique websites each tracking domain appears on
# tracking_domain_counts = {tracker: len(domains) for tracker, domains in tracking_to_domains.items()}

# # Step 8: Get top 20 tracking domains by number of websites
# top_20 = sorted(tracking_domain_counts.items(), key=lambda x: x[1], reverse=True)[:20]

# # Step 9: Display in DataFrame
# top_20_df = pd.DataFrame(top_20, columns=['Tracking Domain', 'Number of Websites'])
# print(top_20_df)
# top_20_df.to_csv("top20.csv", index = False)


# json_file_path = 'disconnect-tracking-protection/entities.json'
# with open(json_file_path, 'r') as f:
#     entities = json.load(f)

# entities = entities["entities"]

# # Build reverse mapping: domain -> company
# domain_to_company = {}
# for company, data in entities.items():
#     for domain in data.get("properties", []):
#         domain_to_company[domain] = company
#     for domain in data.get("resources", []):
#         domain_to_company[domain] = company
# domain_to_company["googletagmanager.com"] = "Google"

# # Step 5: Filter requests on domains_with_requests_only
# filtered_df = df_javascript_reject

# # Step 4: Map each tracking domain_url to set of first-party domains it appears on
# tracking_to_domains = defaultdict(set)
# for _, row in filtered_df.iterrows():
#     tracking_to_domains[row['domain_script_url']].add(row['domain'])

# # Step 5: Map companies to unique first-party domains
# company_to_domains = defaultdict(set)
# for tracker_domain, domain_set in tracking_to_domains.items():
#     company = domain_to_company.get(tracker_domain, tracker_domain)
#     company_to_domains[company].update(domain_set)

# # Step 6: Count unique websites per company
# company_counts = {company: len(domains) for company, domains in company_to_domains.items()}

# # Step 7: Get top 20 companies
# top_20_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:20]

# # Step 8: Display and save results
# top_20_companies_df = pd.DataFrame(top_20_companies, columns=['Company', 'Number of Websites'])
# print(top_20_companies_df)
# top_20_companies_df.to_csv("top20_companies.csv", index=False)

# # Load CSVs
# top20_domains_df = pd.read_csv("top20.csv")  # Columns: Tracking Domain, Number of Websites
# top20_companies_df = pd.read_csv("top20_companies.csv")  # Columns: Company, Number of Websites

# # Build domain-to-company map
# domain_to_company = {
#     domain: company
#     for company, data in entities.items()
#     for domain in data.get("properties", []) + data.get("resources", [])
# }
# domain_to_company["googletagmanager.com"] = "Google"  # Manual fix

# # Map company names to tracking domains
# top20_domains_df["Company"] = top20_domains_df["Tracking Domain"].map(domain_to_company)

# # Calculate percentages
# total = 213  # Predefined value
# print(total)
# top20_domains_df["Percentage"] = (top20_domains_df["Number of Websites"] / total) * 100
# top20_companies_df["Percentage"] = (top20_companies_df["Number of Websites"] / total) * 100
# plt.style.use('default')  # remove seaborn/ggplot background
# # Assign consistent colors to companies
# all_companies = pd.concat([
#     top20_domains_df["Company"],
#     top20_companies_df["Company"]
# ]).dropna().unique()
# color_palette = plt.cm.tab20.colors
# company_colors = {company: color for company, color in zip(all_companies, color_palette)}
# domain_colors = top20_domains_df["Company"].map(company_colors)
# company_colors_bar = top20_companies_df["Company"].map(company_colors)

# plt.figure(figsize=(14, 7))
# ax = plt.gca()

# # Remove grid and background
# ax.grid(False)
# ax.set_facecolor("white")
# plt.gcf().patch.set_facecolor("white")

# # Make full border visible and bold
# for spine in ax.spines.values():
#     spine.set_visible(True)
#     spine.set_linewidth(1.5)
#     spine.set_color("black")


# x1 = np.arange(len(top20_domains_df))
# bars1 = plt.bar(x1, top20_domains_df["Percentage"], color=domain_colors)

# plt.bar_label(bars1, fmt="%.1f", padding=3, fontsize=18)
# plt.ylabel("Percentage of sites", fontsize=20, fontweight="bold")
# plt.xticks(x1, top20_domains_df["Tracking Domain"], rotation=65, ha='right')
# plt.ylim(0, 90)

# plt.text(0.38, 0.95, "Tracking Domains", transform=plt.gca().transAxes,
#          fontsize=32, fontweight="bold", va='top', ha='left',
#          bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

# for label in plt.gca().get_yticklabels():
#     label.set_fontsize(20)
#     label.set_fontweight("bold")
# for label in plt.gca().get_xticklabels():
#     label.set_fontsize(20)
#     label.set_fontweight("bold")

# plt.tight_layout()
# plt.savefig("top20_tracking_domains_percent.pdf")
# plt.show()



# plt.figure(figsize=(14, 7))
# ax = plt.gca()

# # Remove grid and background
# ax.grid(False)
# ax.set_facecolor("white")
# plt.gcf().patch.set_facecolor("white")

# # Make full border visible and bold
# for spine in ax.spines.values():
#     spine.set_visible(True)
#     spine.set_linewidth(1.5)
#     spine.set_color("black")


# x2 = np.arange(len(top20_companies_df))
# bars2 = plt.bar(x2, top20_companies_df["Percentage"], color=company_colors_bar)

# plt.bar_label(bars2, fmt="%.1f", padding=3, fontsize=18)
# plt.ylabel("Percentage of sites", fontsize=20, fontweight="bold")
# plt.xticks(x2, top20_companies_df["Company"], rotation=65, ha='right')
# plt.ylim(0, 90)

# plt.text(0.32, 0.95, "Tracking Companies", transform=plt.gca().transAxes,
#          fontsize=32, fontweight="bold", va='top', ha='left',
#          bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

# for label in plt.gca().get_yticklabels():
#     label.set_fontsize(20)
#     label.set_fontweight("bold")
# for label in plt.gca().get_xticklabels():
#     label.set_fontsize(20)
#     label.set_fontweight("bold")

# plt.tight_layout()
# plt.savefig("top20_tracking_companies_percent.pdf")
# plt.show()




