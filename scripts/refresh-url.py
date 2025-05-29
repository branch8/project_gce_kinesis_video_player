#!/usr/bin/env python3
"""
AWS Kinesis Video Streams HLS URL Refresh Script
Generates fresh HLS streaming URLs and updates the JSON API endpoint
"""

import os
import json
import boto3
from datetime import datetime, timedelta
from pathlib import Path
import sys

def get_env_var(name, default=None):
    """Get environment variable with optional default"""
    value = os.environ.get(name, default)
    if value is None:
        print(f"❌ Missing required environment variable: {name}")
        sys.exit(1)
    return value

def refresh_hls_url():
    """Refresh HLS URL for Kinesis Video Stream"""
    try:
        # Get configuration from environment
        # AWS_REGION and STREAM_NAME come from GitHub Variables (not secrets)
        aws_region = get_env_var('AWS_REGION', 'ap-southeast-2')
        stream_name = get_env_var('STREAM_NAME', 'iot-camera-poc')
        
        print(f"🔄 Refreshing HLS URL for stream: {stream_name}")
        print(f"🌏 Region: {aws_region}")
        
        # Initialize AWS clients
        kinesis_video = boto3.client('kinesisvideo', region_name=aws_region)
        
        # Get data endpoint for HLS streaming
        print("📡 Getting data endpoint...")
        endpoint_response = kinesis_video.get_data_endpoint(
            StreamName=stream_name,
            APIName='GET_HLS_STREAMING_SESSION_URL'
        )
        
        data_endpoint = endpoint_response['DataEndpoint']
        print(f"✅ Data endpoint: {data_endpoint}")
        
        # Get HLS streaming URL
        print("🎥 Generating HLS streaming URL...")
        kinesis_video_archived = boto3.client(
            'kinesisvideo-archived-media',
            endpoint_url=data_endpoint,
            region_name=aws_region
        )
        
        url_response = kinesis_video_archived.get_hls_streaming_session_url(
            StreamName=stream_name,
            PlaybackMode='LIVE',
            Expires=3600  # 1 hour expiration
        )
        
        hls_url = url_response['HLSStreamingSessionURL']
        
        # Prepare stream data
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=1)
        
        stream_data = {
            'hlsUrl': hls_url,
            'expires': expires_at.isoformat() + 'Z',
            'lastUpdated': now.isoformat() + 'Z',
            'streamName': stream_name,
            'region': aws_region,
            'status': 'success'
        }
        
        # Ensure api directory exists
        api_dir = Path(__file__).parent.parent / 'api'
        api_dir.mkdir(exist_ok=True)
        
        # Write to JSON file
        json_file = api_dir / 'stream-url.json'
        with open(json_file, 'w') as f:
            json.dump(stream_data, f, indent=2)
        
        print("✅ Successfully updated stream URL")
        print(f"📅 Expires: {stream_data['expires']}")
        print(f"🔗 URL length: {len(hls_url)} characters")
        print(f"💾 Saved to: {json_file}")
        
        return True
        
    except Exception as error:
        print(f"❌ Failed to refresh HLS URL: {str(error)}")
        
        # Create error file for debugging
        error_data = {
            'error': str(error),
            'error_type': type(error).__name__,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'streamName': stream_name,
            'region': aws_region,
            'status': 'error'
        }
        
        # Ensure api directory exists
        api_dir = Path(__file__).parent.parent / 'api'
        api_dir.mkdir(exist_ok=True)
        
        # Write error file
        error_file = api_dir / 'error.json'
        with open(error_file, 'w') as f:
            json.dump(error_data, f, indent=2)
        
        print(f"💾 Error details saved to: {error_file}")
        sys.exit(1)

if __name__ == '__main__':
    print("🚀 Starting Kinesis Video Stream HLS URL refresh...")
    refresh_hls_url()
    print("🎉 Refresh completed successfully!")