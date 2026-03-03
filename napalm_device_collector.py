#!/usr/bin/env python3
"""
Napalm Network Device Collector for Netbox
Fetches information from network devices using Napalm and writes to Netbox API
"""

import os
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from ipaddress import ip_network, ip_address
from datetime import datetime
import yaml
from napalm import get_network_driver
from napalm.base.exceptions import NapalmException
import pynetbox
from tabulate import tabulate


class Logger:
    """Custom logger configuration"""

    @staticmethod
    def setup(log_file: str = "napalm_collector.log", level: str = "INFO") -> logging.Logger:
        """Setup logging with file and console output"""
        logger = logging.getLogger("NapalmCollector")
        logger.setLevel(getattr(logging, level.upper()))

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

        return logger


class ConfigLoader:
    """Load and parse YAML configuration"""

    def __init__(self, config_file: str, logger: logging.Logger):
        self.config_file = config_file
        self.logger = logger
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load and validate YAML configuration"""
        if not os.path.exists(self.config_file):
            self.logger.error(f"Config file not found: {self.config_file}")
            sys.exit(1)

        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            self.logger.info(f"Loaded configuration from {self.config_file}")
            return config
        except yaml.YAMLError as e:
            self.logger.error(f"YAML parsing error: {e}")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            sys.exit(1)

    def get_netbox_config(self) -> Dict[str, Any]:
        """Get Netbox configuration from config file or environment"""
        netbox_config = self.config.get('netbox', {})

        # Override with environment variables if present
        url = os.getenv('NETBOX_URL') or netbox_config.get('url')
        token = os.getenv('NETBOX_TOKEN') or netbox_config.get('api_token')

        if not url or not token:
            self.logger.error("Netbox URL and API token required (env vars or config.yaml)")
            sys.exit(1)

        return {
            'url': url,
            'token': token,
            'ssl_verify': netbox_config.get('ssl_verify', True)
        }

    def get_napalm_config(self) -> Dict[str, Any]:
        """Get Napalm settings"""
        return self.config.get('napalm', {
            'commands': ['facts', 'interfaces', 'config'],
            'retry_count': 2,
            'timeout': 30
        })

    def get_devices(self) -> List[Dict[str, Any]]:
        """Get and expand device list from config"""
        devices = []
        device_list = self.config.get('devices', [])

        for device_cfg in device_list:
            expanded_devices = self._expand_device(device_cfg)
            devices.extend(expanded_devices)

        self.logger.info(f"Expanded to {len(devices)} device(s) from config")
        return devices

    def _expand_device(self, device_cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Expand single device or IP range to multiple device entries"""
        devices = []

        # Single host
        if 'host' in device_cfg:
            devices.append(device_cfg)

        # IP range (CIDR notation)
        elif 'host_range' in device_cfg:
            try:
                network = ip_network(device_cfg['host_range'], strict=False)
                for ip in network.hosts():  # Skip network and broadcast addresses
                    device = device_cfg.copy()
                    device['host'] = str(ip)
                    device.pop('host_range')
                    if 'name' in device:
                        device['name'] = f"{device['name']}-{ip}"
                    devices.append(device)
                self.logger.debug(f"Expanded range {device_cfg['host_range']} to {len(devices)} hosts")
            except ValueError as e:
                self.logger.error(f"Invalid CIDR range {device_cfg['host_range']}: {e}")

        return devices


class NapalmCollector:
    """Collect information from devices using Napalm"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def get_driver(self, device_cfg: Dict[str, Any]) -> Optional[str]:
        """Get Napalm driver name"""
        manufacturer = device_cfg.get('manufacturer', 'auto').lower()

        # Explicit manufacturer specified
        if manufacturer != 'auto':
            return manufacturer

        # Try auto-detection via SNMP (basic approach)
        # In production, could use device discovery
        self.logger.debug(f"Using auto-detect for {device_cfg['host']}")
        return 'generic'  # Fallback

    def connect_device(self, device_cfg: Dict[str, Any]) -> Optional[Any]:
        """Connect to device using Napalm"""
        host = device_cfg['host']
        timeout = device_cfg.get('timeout', 30)

        credentials = device_cfg.get('credentials', {})
        username = credentials.get('username')

        # Use SSH key or password
        password = credentials.get('password')
        secret = credentials.get('secret', password)
        ssh_key_file = credentials.get('ssh_key')

        connect_params = {
            'hostname': host,
            'username': username,
            'password': password,
            'secret': secret,
            'timeout': timeout,
            'optional_args': {
                'ssh_config_file': credentials.get('ssh_config', None),
                'key_file': ssh_key_file,
                'allow_agent': True,  # Use SSH agent
                'banner_timeout': 20,
                'conn_timeout': timeout
            }
        }

        # Remove None values
        connect_params = {k: v for k, v in connect_params.items()
                         if v is not None and v != {}}

        driver_name = self.get_driver(device_cfg)

        try:
            driver_class = get_network_driver(driver_name)
            device = driver_class(**connect_params)
            device.open()
            self.logger.info(f"Connected to {host} using driver: {driver_name}")
            return device
        except Exception as e:
            self.logger.error(f"Failed to connect to {host}: {e}")
            return None

    def collect_facts(self, device: Any) -> Dict[str, Any]:
        """Get device facts"""
        try:
            facts = device.get_facts()
            self.logger.debug(f"Successfully retrieved facts from {device.hostname}")
            return facts
        except Exception as e:
            self.logger.warning(f"Failed to get facts from {device.hostname}: {e}")
            return {}

    def collect_interfaces(self, device: Any) -> Dict[str, Any]:
        """Get interface information"""
        try:
            interfaces = device.get_interfaces()
            self.logger.debug(f"Retrieved {len(interfaces)} interfaces from {device.hostname}")
            return interfaces
        except Exception as e:
            self.logger.warning(f"Failed to get interfaces from {device.hostname}: {e}")
            return {}

    def collect_config(self, device: Any) -> Optional[str]:
        """Get running configuration"""
        try:
            config = device.get_config(retrieve='running')
            running_config = config.get('running', '')
            self.logger.debug(f"Retrieved running config from {device.hostname}")
            return running_config
        except Exception as e:
            self.logger.warning(f"Failed to get config from {device.hostname}: {e}")
            return None

    def collect_bgp(self, device: Any) -> Dict[str, Any]:
        """Get BGP neighbor information"""
        try:
            bgp_data = device.get_bgp_neighbors()
            self.logger.debug(f"Retrieved BGP data from {device.hostname}")
            return bgp_data
        except Exception as e:
            self.logger.debug(f"BGP not available on {device.hostname}: {e}")
            return {}

    def collect_all(self, device_cfg: Dict[str, Any], commands: List[str]) -> Dict[str, Any]:
        """Collect all requested information from a device"""
        device = self.connect_device(device_cfg)
        if not device:
            return {'error': 'Connection failed'}

        collected_data = {
            'host': device_cfg['host'],
            'name': device_cfg.get('name', device_cfg['host']),
            'manufacturer': device_cfg.get('manufacturer', 'unknown'),
            'collected_at': datetime.now().isoformat()
        }

        try:
            if 'facts' in commands:
                collected_data['facts'] = self.collect_facts(device)

            if 'interfaces' in commands:
                collected_data['interfaces'] = self.collect_interfaces(device)

            if 'config' in commands:
                collected_data['config'] = self.collect_config(device)

            if 'bgp' in commands:
                collected_data['bgp'] = self.collect_bgp(device)

        finally:
            try:
                device.close()
            except:
                pass

        return collected_data


class NetboxWriter:
    """Write collected data to Netbox API"""

    def __init__(self, netbox_config: Dict[str, Any], logger: logging.Logger):
        self.logger = logger
        try:
            self.api = pynetbox.api(
                netbox_config['url'],
                token=netbox_config['token'],
                ssl_verify=netbox_config.get('ssl_verify', True)
            )
            self.logger.info(f"Connected to Netbox at {netbox_config['url']}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Netbox: {e}")
            self.api = None

    def write_device(self, collected_data: Dict[str, Any], dry_run: bool = False) -> bool:
        """Write or update device in Netbox"""
        if not self.api or 'error' in collected_data:
            return False

        host = collected_data['host']
        facts = collected_data.get('facts', {})

        if not facts:
            self.logger.warning(f"No facts available for {host}, skipping Netbox write")
            return False

        device_data = {
            'name': collected_data['name'],
            'device_type': self._get_or_create_device_type(facts),
            'site': self._get_or_create_site(facts),
            'manufacturer': self._get_or_create_manufacturer(facts),
            'serial': facts.get('serial_number', ''),
            'asset_tag': facts.get('serial_number', ''),
            'comments': f"Auto-collected by Napalm on {collected_data['collected_at']}"
        }

        try:
            if dry_run:
                self.logger.info(f"[DRY-RUN] Would write device {host} to Netbox: {device_data}")
                return True

            # Check if device exists
            try:
                device = self.api.dcim.devices.get(name=device_data['name'])
                if device:
                    self.logger.info(f"Updating existing device {device_data['name']}")
                    device.update(device_data)
                    return True
            except:
                pass

            # Create new device
            self.logger.info(f"Creating new device {device_data['name']} in Netbox")
            self.api.dcim.devices.create(**device_data)
            return True

        except Exception as e:
            self.logger.error(f"Failed to write device {host} to Netbox: {e}")
            return False

    def _get_or_create_manufacturer(self, facts: Dict[str, Any]) -> Optional[int]:
        """Get manufacturer ID from Netbox or create it"""
        vendor = facts.get('vendor', 'Unknown')
        try:
            mfg = self.api.dcim.manufacturers.get(name=vendor)
            if mfg:
                return mfg.id
        except:
            pass

        # Try to create if doesn't exist
        try:
            mfg = self.api.dcim.manufacturers.create(name=vendor, slug=vendor.lower())
            return mfg.id
        except Exception as e:
            self.logger.debug(f"Could not create manufacturer {vendor}: {e}")
            return None

    def _get_or_create_site(self, facts: Dict[str, Any]) -> Optional[int]:
        """Get or create site (using default 'Default')"""
        try:
            site = self.api.dcim.sites.get(name='Default')
            if site:
                return site.id
        except:
            pass

        try:
            site = self.api.dcim.sites.create(name='Default', slug='default')
            return site.id
        except Exception as e:
            self.logger.debug(f"Could not get/create default site: {e}")
            return None

    def _get_or_create_device_type(self, facts: Dict[str, Any]) -> Optional[int]:
        """Get device type or create generic one"""
        model = facts.get('model', 'Unknown')
        try:
            dtype = self.api.dcim.device_types.get(model=model)
            if dtype:
                return dtype.id
        except:
            pass

        # Create generic device type
        try:
            mfg = self._get_or_create_manufacturer(facts)
            dtype = self.api.dcim.device_types.create(
                manufacturer=mfg,
                model=model,
                slug=model.lower().replace(' ', '-')
            )
            return dtype.id
        except Exception as e:
            self.logger.debug(f"Could not create device type {model}: {e}")
            return None


class NapalmNetboxOrchestrator:
    """Main orchestrator for the collection process"""

    def __init__(self, config_file: str, verbose: bool = False, dry_run: bool = False):
        self.verbose = verbose
        self.dry_run = dry_run

        log_level = "DEBUG" if verbose else "INFO"
        self.logger = Logger.setup(level=log_level)

        self.config_loader = ConfigLoader(config_file, self.logger)
        self.netbox_config = self.config_loader.get_netbox_config()
        self.napalm_config = self.config_loader.get_napalm_config()

        self.collector = NapalmCollector(self.logger)
        self.writer = NetboxWriter(self.netbox_config, self.logger)

        self.results = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'devices': []
        }

    def run(self):
        """Execute the collection and write process"""
        self.logger.info("=" * 60)
        self.logger.info("Starting Napalm Network Device Collection")
        self.logger.info(f"Dry-run mode: {self.dry_run}")
        self.logger.info("=" * 60)

        devices = self.config_loader.get_devices()
        commands = self.napalm_config.get('commands', ['facts'])

        self.logger.info(f"Processing {len(devices)} device(s)...")

        for idx, device_cfg in enumerate(devices, 1):
            device_name = device_cfg.get('name', device_cfg['host'])
            self.logger.info(f"\n[{idx}/{len(devices)}] Processing {device_name}")

            # Collect data
            collected_data = self.collector.collect_all(device_cfg, commands)

            if 'error' in collected_data:
                self.logger.error(f"  ✗ Collection failed: {collected_data['error']}")
                self.results['failed'] += 1
                self.results['devices'].append({
                    'name': device_name,
                    'status': 'failed',
                    'error': collected_data['error']
                })
                continue

            # Write to Netbox
            if self.writer.api:
                success = self.writer.write_device(collected_data, self.dry_run)
                if success:
                    self.logger.info(f"  ✓ Successfully processed")
                    self.results['success'] += 1
                    self.results['devices'].append({
                        'name': device_name,
                        'status': 'success'
                    })
                else:
                    self.logger.error(f"  ✗ Netbox write failed")
                    self.results['failed'] += 1
                    self.results['devices'].append({
                        'name': device_name,
                        'status': 'failed',
                        'error': 'Netbox write failed'
                    })
            else:
                self.logger.warning(f"  ⚠ Netbox not available, skipping write")
                self.results['skipped'] += 1

        self._print_summary()

    def _print_summary(self):
        """Print summary of the collection"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("Collection Summary")
        self.logger.info("=" * 60)

        summary_data = [
            ['Successful', self.results['success']],
            ['Failed', self.results['failed']],
            ['Skipped', self.results['skipped']],
            ['Total', len(self.results['devices'])]
        ]

        print(tabulate(summary_data, headers=['Status', 'Count'], tablefmt='grid'))

        if self.results['failed'] > 0:
            self.logger.warning("\nFailed devices:")
            for device in self.results['devices']:
                if device['status'] == 'failed':
                    error = device.get('error', 'Unknown error')
                    self.logger.warning(f"  - {device['name']}: {error}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Collect network device information using Napalm and write to Netbox',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with config file
  python napalm_device_collector.py --config config.yaml

  # Verbose output and dry-run mode
  python napalm_device_collector.py --config config.yaml --verbose --dry-run

  # With Netbox credentials via environment variables
  export NETBOX_URL="https://netbox.example.com"
  export NETBOX_TOKEN="0123456789abcdef"
  python napalm_device_collector.py --config config.yaml
        """
    )

    parser.add_argument(
        '--config',
        required=True,
        help='Path to YAML configuration file'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose/debug output'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry-run mode: show what would be done without actually writing to Netbox'
    )

    args = parser.parse_args()

    orchestrator = NapalmNetboxOrchestrator(
        config_file=args.config,
        verbose=args.verbose,
        dry_run=args.dry_run
    )
    orchestrator.run()


if __name__ == '__main__':
    main()
