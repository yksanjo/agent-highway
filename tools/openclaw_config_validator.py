#!/usr/bin/env python3
"""
OpenClaw Configuration Validator

A comprehensive validation tool for openclaw.json configuration files.
Validates schema, security, best practices, and connectivity.

Usage:
    python openclaw_config_validator.py <config_path> [options]
    python openclaw_config_validator.py ~/.openclaw/openclaw.json
    python openclaw_config_validator.py config.json --fix --strict
    python openclaw_config_validator.py config.json --output json
"""

import argparse
import json
import os
import re
import sys
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IssueType(Enum):
    """Types of validation issues."""
    SCHEMA = "schema"
    SECURITY = "security"
    BEST_PRACTICE = "best_practice"
    CONNECTIVITY = "connectivity"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    severity: Severity
    issue_type: IssueType
    path: str
    message: str
    suggestion: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class ValidationResult:
    """Results of validation."""
    issues: List[ValidationIssue] = field(default_factory=list)
    fixed_issues: List[ValidationIssue] = field(default_factory=list)
    
    def add_issue(self, issue: ValidationIssue):
        self.issues.append(issue)
    
    def add_fixed(self, issue: ValidationIssue):
        self.fixed_issues.append(issue)
    
    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]
    
    @property
    def infos(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.INFO]
    
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_issues": len(self.issues),
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "infos": len(self.infos),
                "fixed": len(self.fixed_issues),
                "valid": not self.has_errors()
            },
            "issues": [
                {
                    "severity": i.severity.value,
                    "type": i.issue_type.value,
                    "path": i.path,
                    "message": i.message,
                    "suggestion": i.suggestion,
                    "auto_fixable": i.auto_fixable
                }
                for i in self.issues
            ],
            "fixed": [
                {
                    "type": i.issue_type.value,
                    "path": i.path,
                    "message": i.message
                }
                for i in self.fixed_issues
            ]
        }


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'
    
    @classmethod
    def disable(cls):
        cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = ''
        cls.MAGENTA = cls.CYAN = cls.WHITE = cls.BOLD = ''
        cls.DIM = cls.RESET = ''


class OpenClawValidator:
    """Main validator class for openclaw.json configurations."""
    
    # Valid channel types
    VALID_CHANNEL_TYPES = {'telegram', 'discord'}
    
    # Valid gateway modes
    VALID_GATEWAY_MODES = {'local', 'cloudflare'}
    
    # Valid auth modes
    VALID_AUTH_MODES = {'token', 'jwt', 'oauth', 'none'}
    
    # DM policies
    VALID_DM_POLICIES = {'pairing', 'open', 'closed'}
    
    # Group policies
    VALID_GROUP_POLICIES = {'allowlist', 'blocklist', 'open'}
    
    # Stream modes
    VALID_STREAM_MODES = {'full', 'partial', 'none'}
    
    def __init__(self, strict: bool = False):
        self.strict = strict
        self.result = ValidationResult()
        self.config: Dict[str, Any] = {}
        self.config_path: Optional[Path] = None
    
    def validate(self, config_path: Path) -> ValidationResult:
        """Run all validation checks."""
        self.config_path = config_path
        
        # Load config
        if not self._load_config(config_path):
            return self.result
        
        # Run validation checks
        self._validate_schema()
        self._validate_channels()
        self._validate_gateway()
        self._validate_talk()
        self._validate_security()
        self._validate_best_practices()
        self._validate_plugins()
        
        return self.result
    
    def _load_config(self, path: Path) -> bool:
        """Load and parse the configuration file."""
        try:
            if not path.exists():
                self.result.add_issue(ValidationIssue(
                    severity=Severity.ERROR,
                    issue_type=IssueType.SCHEMA,
                    path="",
                    message=f"Configuration file not found: {path}"
                ))
                return False
            
            with open(path, 'r') as f:
                self.config = json.load(f)
            
            if not isinstance(self.config, dict):
                self.result.add_issue(ValidationIssue(
                    severity=Severity.ERROR,
                    issue_type=IssueType.SCHEMA,
                    path="",
                    message="Configuration must be a JSON object"
                ))
                return False
            
            return True
            
        except json.JSONDecodeError as e:
            self.result.add_issue(ValidationIssue(
                severity=Severity.ERROR,
                issue_type=IssueType.SCHEMA,
                path="",
                message=f"Invalid JSON: {e}"
            ))
            return False
        except Exception as e:
            self.result.add_issue(ValidationIssue(
                severity=Severity.ERROR,
                issue_type=IssueType.SCHEMA,
                path="",
                message=f"Failed to read config: {e}"
            ))
            return False
    
    def _validate_schema(self):
        """Validate required fields and structure."""
        # Required top-level fields
        required_fields = {'channels', 'gateway', 'talk'}
        optional_fields = {'meta', 'wizard', 'agents', 'messages', 'commands', 'plugins'}
        
        # Check for required fields
        for field in required_fields:
            if field not in self.config:
                self.result.add_issue(ValidationIssue(
                    severity=Severity.ERROR,
                    issue_type=IssueType.SCHEMA,
                    path=field,
                    message=f"Required field '{field}' is missing",
                    suggestion=f"Add the '{field}' section to your configuration"
                ))
        
        # Check for unknown fields
        all_known = required_fields | optional_fields
        for field in self.config:
            if field not in all_known:
                self.result.add_issue(ValidationIssue(
                    severity=Severity.WARNING if not self.strict else Severity.ERROR,
                    issue_type=IssueType.SCHEMA,
                    path=field,
                    message=f"Unknown field '{field}'",
                    suggestion="Remove unknown fields or check for typos"
                ))
    
    def _validate_channels(self):
        """Validate channel configurations."""
        channels = self.config.get('channels', {})
        
        if not channels:
            self.result.add_issue(ValidationIssue(
                severity=Severity.WARNING,
                issue_type=IssueType.SCHEMA,
                path="channels",
                message="No channels configured",
                suggestion="Add at least one channel (telegram or discord)"
            ))
            return
        
        # Check channel types
        for channel_name, channel_config in channels.items():
            if channel_name not in self.VALID_CHANNEL_TYPES:
                self.result.add_issue(ValidationIssue(
                    severity=Severity.WARNING,
                    issue_type=IssueType.SCHEMA,
                    path=f"channels.{channel_name}",
                    message=f"Unknown channel type: {channel_name}",
                    suggestion=f"Valid channel types: {', '.join(self.VALID_CHANNEL_TYPES)}"
                ))
                continue
            
            self._validate_channel_config(channel_name, channel_config)
    
    def _validate_channel_config(self, name: str, config: Dict[str, Any]):
        """Validate individual channel configuration."""
        path_prefix = f"channels.{name}"
        
        # Check enabled status
        if 'enabled' not in config:
            self.result.add_issue(ValidationIssue(
                severity=Severity.INFO,
                issue_type=IssueType.BEST_PRACTICE,
                path=f"{path_prefix}.enabled",
                message=f"'enabled' not specified for {name}, defaults to true"
            ))
        
        # Channel-specific validation
        if name == 'telegram':
            self._validate_telegram_config(config)
        elif name == 'discord':
            self._validate_discord_config(config)
    
    def _validate_telegram_config(self, config: Dict[str, Any]):
        """Validate Telegram-specific configuration."""
        # Bot token validation
        token = config.get('botToken')
        if token:
            if self._is_env_reference(token):
                # Token is an env reference - valid in non-strict mode
                if self.strict:
                    self.result.add_issue(ValidationIssue(
                        severity=Severity.INFO,
                        issue_type=IssueType.SECURITY,
                        path="channels.telegram.botToken",
                        message="Using environment variable for Telegram token (good!)"
                    ))
            else:
                # Check token format (should be digits:alphanumeric)
                if not re.match(r'^\d+:[A-Za-z0-9_-]{35,}$', str(token)):
                    self.result.add_issue(ValidationIssue(
                        severity=Severity.WARNING,
                        issue_type=IssueType.SCHEMA,
                        path="channels.telegram.botToken",
                        message="Telegram bot token format appears invalid",
                        suggestion="Token should match pattern: digits:alphanumeric (at least 35 chars)"
                    ))
                
                # Check for plaintext secrets in strict mode
                if self.strict:
                    self.result.add_issue(ValidationIssue(
                        severity=Severity.ERROR,
                        issue_type=IssueType.SECURITY,
                        path="channels.telegram.botToken",
                        message="Telegram bot token should not be stored in plain text",
                        suggestion="Use environment variable: ${TELEGRAM_BOT_TOKEN}",
                        auto_fixable=True
                    ))
        elif config.get('enabled', True):
            self.result.add_issue(ValidationIssue(
                severity=Severity.ERROR,
                issue_type=IssueType.SCHEMA,
                path="channels.telegram.botToken",
                message="Telegram bot token is required when enabled",
                suggestion="Add botToken or set enabled: false"
            ))
        
        # DM policy validation
        dm_policy = config.get('dmPolicy')
        if dm_policy and dm_policy not in self.VALID_DM_POLICIES:
            self.result.add_issue(ValidationIssue(
                severity=Severity.WARNING,
                issue_type=IssueType.SCHEMA,
                path="channels.telegram.dmPolicy",
                message=f"Invalid DM policy: {dm_policy}",
                suggestion=f"Valid policies: {', '.join(self.VALID_DM_POLICIES)}"
            ))
        
        # Group policy validation
        group_policy = config.get('groupPolicy')
        if group_policy and group_policy not in self.VALID_GROUP_POLICIES:
            self.result.add_issue(ValidationIssue(
                severity=Severity.WARNING,
                issue_type=IssueType.SCHEMA,
                path="channels.telegram.groupPolicy",
                message=f"Invalid group policy: {group_policy}",
                suggestion=f"Valid policies: {', '.join(self.VALID_GROUP_POLICIES)}"
            ))
        
        # Stream mode validation
        stream_mode = config.get('streamMode')
        if stream_mode and stream_mode not in self.VALID_STREAM_MODES:
            self.result.add_issue(ValidationIssue(
                severity=Severity.WARNING,
                issue_type=IssueType.SCHEMA,
                path="channels.telegram.streamMode",
                message=f"Invalid stream mode: {stream_mode}",
                suggestion=f"Valid modes: {', '.join(self.VALID_STREAM_MODES)}"
            ))
    
    def _validate_discord_config(self, config: Dict[str, Any]):
        """Validate Discord-specific configuration."""
        # Token validation
        token = config.get('token')
        if token:
            if self._is_env_reference(token):
                # Token is an env reference - valid in non-strict mode
                if self.strict:
                    self.result.add_issue(ValidationIssue(
                        severity=Severity.INFO,
                        issue_type=IssueType.SECURITY,
                        path="channels.discord.token",
                        message="Using environment variable for Discord token (good!)"
                    ))
            else:
                # Discord tokens are base64-encoded and typically long
                if len(str(token)) < 50:
                    self.result.add_issue(ValidationIssue(
                        severity=Severity.WARNING,
                        issue_type=IssueType.SCHEMA,
                        path="channels.discord.token",
                        message="Discord token appears too short",
                        suggestion="Discord tokens are typically 59+ characters"
                    ))
                
                # Check for plaintext secrets
                if self.strict:
                    self.result.add_issue(ValidationIssue(
                        severity=Severity.ERROR,
                        issue_type=IssueType.SECURITY,
                        path="channels.discord.token",
                        message="Discord token should not be stored in plain text",
                        suggestion="Use environment variable: ${DISCORD_TOKEN}",
                        auto_fixable=True
                    ))
        elif config.get('enabled', True):
            self.result.add_issue(ValidationIssue(
                severity=Severity.ERROR,
                issue_type=IssueType.SCHEMA,
                path="channels.discord.token",
                message="Discord token is required when enabled",
                suggestion="Add token or set enabled: false"
            ))
        
        # Intents validation
        intents = config.get('intents', {})
        if not intents.get('guildMembers') and config.get('enabled', True):
            self.result.add_issue(ValidationIssue(
                severity=Severity.INFO,
                issue_type=IssueType.BEST_PRACTICE,
                path="channels.discord.intents",
                message="guildMembers intent not enabled",
                suggestion="Enable guildMembers intent for better user recognition"
            ))
    
    def _validate_gateway(self):
        """Validate gateway configuration."""
        gateway = self.config.get('gateway', {})
        
        if not gateway:
            self.result.add_issue(ValidationIssue(
                severity=Severity.ERROR,
                issue_type=IssueType.SCHEMA,
                path="gateway",
                message="Gateway configuration is missing"
            ))
            return
        
        # Mode validation
        mode = gateway.get('mode')
        if mode not in self.VALID_GATEWAY_MODES:
            self.result.add_issue(ValidationIssue(
                severity=Severity.ERROR,
                issue_type=IssueType.SCHEMA,
                path="gateway.mode",
                message=f"Invalid gateway mode: {mode}",
                suggestion=f"Valid modes: {', '.join(self.VALID_GATEWAY_MODES)}"
            ))
        
        # Bind validation
        bind = gateway.get('bind')
        if bind and bind not in {'lan', 'localhost', '0.0.0.0', '127.0.0.1'}:
            if not self._is_valid_ip(bind):
                self.result.add_issue(ValidationIssue(
                    severity=Severity.WARNING,
                    issue_type=IssueType.SCHEMA,
                    path="gateway.bind",
                    message=f"Unusual bind address: {bind}",
                    suggestion="Use 'lan', 'localhost', or a valid IP address"
                ))
        
        # Auth validation
        auth = gateway.get('auth', {})
        auth_mode = auth.get('mode')
        
        if auth_mode not in self.VALID_AUTH_MODES:
            self.result.add_issue(ValidationIssue(
                severity=Severity.ERROR,
                issue_type=IssueType.SCHEMA,
                path="gateway.auth.mode",
                message=f"Invalid auth mode: {auth_mode}",
                suggestion=f"Valid modes: {', '.join(self.VALID_AUTH_MODES)}"
            ))
        
        # Token validation
        if auth_mode == 'token' or auth_mode is None:
            token = auth.get('token')
            if token:
                # Check token entropy
                entropy = self._calculate_entropy(token)
                if entropy < 3.5:
                    self.result.add_issue(ValidationIssue(
                        severity=Severity.WARNING if not self.strict else Severity.ERROR,
                        issue_type=IssueType.SECURITY,
                        path="gateway.auth.token",
                        message=f"Gateway token has low entropy ({entropy:.2f} bits/char)",
                        suggestion="Use a cryptographically secure random token (at least 32 chars)"
                    ))
                
                # Check for plaintext in strict mode
                if self.strict and not self._is_env_reference(token):
                    self.result.add_issue(ValidationIssue(
                        severity=Severity.ERROR,
                        issue_type=IssueType.SECURITY,
                        path="gateway.auth.token",
                        message="Gateway auth token should not be stored in plain text",
                        suggestion="Use environment variable: ${GATEWAY_AUTH_TOKEN}",
                        auto_fixable=True
                    ))
    
    def _validate_talk(self):
        """Validate talk configuration."""
        talk = self.config.get('talk', {})
        
        if not talk:
            self.result.add_issue(ValidationIssue(
                severity=Severity.ERROR,
                issue_type=IssueType.SCHEMA,
                path="talk",
                message="Talk configuration is missing"
            ))
            return
        
        api_key = talk.get('apiKey')
        if api_key:
            # Check for plaintext
            if not self._is_env_reference(api_key):
                self.result.add_issue(ValidationIssue(
                    severity=Severity.WARNING if not self.strict else Severity.ERROR,
                    issue_type=IssueType.SECURITY,
                    path="talk.apiKey",
                    message="API key should ideally be stored in environment variable",
                    suggestion="Use environment variable: ${TALK_API_KEY}",
                    auto_fixable=True
                ))
            
            # Check key entropy
            entropy = self._calculate_entropy(api_key)
            if entropy < 3.0:
                self.result.add_issue(ValidationIssue(
                    severity=Severity.WARNING,
                    issue_type=IssueType.SECURITY,
                    path="talk.apiKey",
                    message=f"API key has low entropy ({entropy:.2f} bits/char)",
                    suggestion="Generate a stronger API key"
                ))
    
    def _validate_security(self):
        """Validate security-related settings."""
        # Check for any HTTPS URLs
        def check_https_urls(obj: Any, path: str = ""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    check_https_urls(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_https_urls(item, f"{path}[{i}]")
            elif isinstance(obj, str):
                if obj.startswith('http://') and not obj.startswith('http://localhost'):
                    self.result.add_issue(ValidationIssue(
                        severity=Severity.WARNING if not self.strict else Severity.ERROR,
                        issue_type=IssueType.SECURITY,
                        path=path,
                        message=f"Non-HTTPS URL detected: {obj}",
                        suggestion="Use HTTPS for all external endpoints"
                    ))
        
        check_https_urls(self.config)
        
        # Check for suspicious patterns that might be secrets
        secret_patterns = [
            (r'password\s*[=:]\s*["\'][^"\']+["\']', "password"),
            (r'secret\s*[=:]\s*["\'][^"\']+["\']', "secret"),
            (r'private_key\s*[=:]\s*["\'][^"\']+["\']', "private_key"),
        ]
        
        config_str = json.dumps(self.config)
        for pattern, name in secret_patterns:
            if re.search(pattern, config_str, re.IGNORECASE):
                self.result.add_issue(ValidationIssue(
                    severity=Severity.WARNING,
                    issue_type=IssueType.SECURITY,
                    path="",
                    message=f"Potential hardcoded {name} detected in configuration",
                    suggestion=f"Move {name} to environment variables"
                ))
    
    def _validate_best_practices(self):
        """Validate best practice configurations."""
        # Agents configuration
        agents = self.config.get('agents', {})
        defaults = agents.get('defaults', {})
        
        # Check maxConcurrent
        max_concurrent = defaults.get('maxConcurrent')
        if max_concurrent is not None:
            if max_concurrent > 10:
                self.result.add_issue(ValidationIssue(
                    severity=Severity.WARNING,
                    issue_type=IssueType.BEST_PRACTICE,
                    path="agents.defaults.maxConcurrent",
                    message=f"High concurrent agent limit: {max_concurrent}",
                    suggestion="Consider reducing to 5-8 for resource management"
                ))
            elif max_concurrent < 1:
                self.result.add_issue(ValidationIssue(
                    severity=Severity.ERROR,
                    issue_type=IssueType.SCHEMA,
                    path="agents.defaults.maxConcurrent",
                    message=f"Invalid concurrent agent limit: {max_concurrent}"
                ))
        
        # Check subagent limits
        subagents = defaults.get('subagents', {})
        subagent_max = subagents.get('maxConcurrent')
        if subagent_max is not None and subagent_max > 20:
            self.result.add_issue(ValidationIssue(
                severity=Severity.WARNING,
                issue_type=IssueType.BEST_PRACTICE,
                path="agents.defaults.subagents.maxConcurrent",
                message=f"High subagent concurrent limit: {subagent_max}",
                suggestion="Consider reducing to 8-12 to prevent resource exhaustion"
            ))
        
        # Messages configuration
        messages = self.config.get('messages', {})
        if 'ackReactionScope' not in messages:
            self.result.add_issue(ValidationIssue(
                severity=Severity.INFO,
                issue_type=IssueType.BEST_PRACTICE,
                path="messages.ackReactionScope",
                message="ackReactionScope not configured",
                suggestion="Set to 'group-mentions' or 'all' based on your preference"
            ))
        
        # Commands configuration
        commands = self.config.get('commands', {})
        if commands.get('restart') is False:
            self.result.add_issue(ValidationIssue(
                severity=Severity.INFO,
                issue_type=IssueType.BEST_PRACTICE,
                path="commands.restart",
                message="Restart command is disabled",
                suggestion="Consider enabling restart command for easier management"
            ))
        
        # Meta information
        meta = self.config.get('meta', {})
        if not meta.get('lastTouchedVersion'):
            self.result.add_issue(ValidationIssue(
                severity=Severity.INFO,
                issue_type=IssueType.BEST_PRACTICE,
                path="meta.lastTouchedVersion",
                message="Configuration version not tracked",
                suggestion="Keep version info for easier debugging"
            ))
    
    def _validate_plugins(self):
        """Validate plugin configurations."""
        plugins = self.config.get('plugins', {})
        entries = plugins.get('entries', {})
        
        if not entries:
            self.result.add_issue(ValidationIssue(
                severity=Severity.INFO,
                issue_type=IssueType.BEST_PRACTICE,
                path="plugins.entries",
                message="No plugins configured",
                suggestion="Add plugins to extend functionality"
            ))
            return
        
        # Check for plugin compatibility
        channels = self.config.get('channels', {})
        
        # Telegram plugin should match channel config
        telegram_plugin = entries.get('telegram', {})
        telegram_channel = channels.get('telegram', {})
        if telegram_plugin.get('enabled') and not telegram_channel.get('enabled'):
            self.result.add_issue(ValidationIssue(
                severity=Severity.WARNING,
                issue_type=IssueType.BEST_PRACTICE,
                path="plugins.entries.telegram",
                message="Telegram plugin enabled but channel is disabled",
                suggestion="Enable channels.telegram or disable the plugin"
            ))
        
        # Discord plugin should match channel config
        discord_plugin = entries.get('discord', {})
        discord_channel = channels.get('discord', {})
        if discord_plugin.get('enabled') and not discord_channel.get('enabled'):
            self.result.add_issue(ValidationIssue(
                severity=Severity.WARNING,
                issue_type=IssueType.BEST_PRACTICE,
                path="plugins.entries.discord",
                message="Discord plugin enabled but channel is disabled",
                suggestion="Enable channels.discord or disable the plugin"
            ))
    
    def _is_env_reference(self, value: str) -> bool:
        """Check if value is an environment variable reference."""
        if not isinstance(value, str):
            return False
        # Pattern: ${VAR_NAME} or $VAR_NAME
        return bool(re.match(r'^\$\{?[A-Za-z_][A-Za-z0-9_]*\}?$', value.strip()))
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not text:
            return 0.0
        
        # Calculate frequency of each character
        freq = {}
        for char in text:
            freq[char] = freq.get(char, 0) + 1
        
        # Calculate entropy
        length = len(text)
        entropy = 0.0
        for count in freq.values():
            p = count / length
            entropy -= p * math.log2(p)
        
        return entropy
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Check if string is a valid IP address."""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            except ValueError:
                return False
        return True
    
    def apply_fixes(self, config_path: Path) -> bool:
        """Apply auto-fixes to configuration."""
        if not self.config:
            return False
        
        modified = False
        
        # Fix: Move plaintext tokens to env references
        channels = self.config.get('channels', {})
        
        # Telegram token
        telegram = channels.get('telegram', {})
        if telegram.get('botToken') and not self._is_env_reference(telegram['botToken']):
            old_value = telegram['botToken']
            telegram['botToken'] = '${TELEGRAM_BOT_TOKEN}'
            self.result.add_fixed(ValidationIssue(
                severity=Severity.INFO,
                issue_type=IssueType.SECURITY,
                path="channels.telegram.botToken",
                message=f"Replaced plaintext token with environment variable reference"
            ))
            modified = True
        
        # Discord token
        discord = channels.get('discord', {})
        if discord.get('token') and not self._is_env_reference(discord['token']):
            old_value = discord['token']
            discord['token'] = '${DISCORD_TOKEN}'
            self.result.add_fixed(ValidationIssue(
                severity=Severity.INFO,
                issue_type=IssueType.SECURITY,
                path="channels.discord.token",
                message=f"Replaced plaintext token with environment variable reference"
            ))
            modified = True
        
        # Gateway auth token
        gateway = self.config.get('gateway', {})
        auth = gateway.get('auth', {})
        if auth.get('token') and not self._is_env_reference(auth['token']):
            old_value = auth['token']
            auth['token'] = '${GATEWAY_AUTH_TOKEN}'
            self.result.add_fixed(ValidationIssue(
                severity=Severity.INFO,
                issue_type=IssueType.SECURITY,
                path="gateway.auth.token",
                message=f"Replaced plaintext token with environment variable reference"
            ))
            modified = True
        
        # Talk API key
        talk = self.config.get('talk', {})
        if talk.get('apiKey') and not self._is_env_reference(talk['apiKey']):
            old_value = talk['apiKey']
            talk['apiKey'] = '${TALK_API_KEY}'
            self.result.add_fixed(ValidationIssue(
                severity=Severity.INFO,
                issue_type=IssueType.SECURITY,
                path="talk.apiKey",
                message=f"Replaced plaintext API key with environment variable reference"
            ))
            modified = True
        
        # Write modified config
        if modified:
            try:
                # Create backup
                backup_path = config_path.with_suffix('.json.backup')
                with open(backup_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
                
                # Write new config
                with open(config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
                
                return True
            except Exception as e:
                self.result.add_issue(ValidationIssue(
                    severity=Severity.ERROR,
                    issue_type=IssueType.SCHEMA,
                    path="",
                    message=f"Failed to write fixed config: {e}"
                ))
                return False
        
        return False


def print_results(result: ValidationResult, output_format: str = "cli"):
    """Print validation results."""
    if output_format == "json":
        print(json.dumps(result.to_dict(), indent=2))
        return
    
    # CLI output with colors
    summary = result.to_dict()['summary']
    
    print()
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  OpenClaw Configuration Validation Report{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    print()
    
    # Summary
    status_color = Colors.GREEN if summary['valid'] else Colors.RED
    status_text = "✓ VALID" if summary['valid'] else "✗ INVALID"
    print(f"  Status: {status_color}{status_text}{Colors.RESET}")
    print(f"  Total Issues: {summary['total_issues']}")
    print(f"    {Colors.RED}Errors: {summary['errors']}{Colors.RESET}")
    print(f"    {Colors.YELLOW}Warnings: {summary['warnings']}{Colors.RESET}")
    print(f"    {Colors.BLUE}Infos: {summary['infos']}{Colors.RESET}")
    
    if summary['fixed'] > 0:
        print(f"    {Colors.GREEN}Auto-fixed: {summary['fixed']}{Colors.RESET}")
    
    print()
    
    # Detailed issues
    if result.issues:
        print(f"{Colors.BOLD}Detailed Issues:{Colors.RESET}")
        print()
        
        for issue in result.issues:
            if issue.severity == Severity.ERROR:
                severity_color = Colors.RED
                icon = "✗"
            elif issue.severity == Severity.WARNING:
                severity_color = Colors.YELLOW
                icon = "⚠"
            else:
                severity_color = Colors.BLUE
                icon = "ℹ"
            
            print(f"  {severity_color}{icon} [{issue.issue_type.value.upper()}]{Colors.RESET} {issue.path}")
            print(f"     {issue.message}")
            if issue.suggestion:
                print(f"     {Colors.DIM}→ {issue.suggestion}{Colors.RESET}")
            if issue.auto_fixable:
                print(f"     {Colors.GREEN}[Auto-fixable with --fix]{Colors.RESET}")
            print()
    
    # Fixed issues
    if result.fixed_issues:
        print(f"{Colors.BOLD}{Colors.GREEN}Applied Fixes:{Colors.RESET}")
        print()
        for issue in result.fixed_issues:
            print(f"  {Colors.GREEN}✓{Colors.RESET} [{issue.issue_type.value.upper()}] {issue.path}")
            print(f"     {issue.message}")
        print()
    
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Validate openclaw.json configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ~/.openclaw/openclaw.json
  %(prog)s config.json --fix --strict
  %(prog)s config.json --output json
  %(prog)s config.json --no-color
        """
    )
    
    parser.add_argument('config', type=Path, help='Path to openclaw.json file')
    parser.add_argument('--fix', action='store_true', 
                        help='Auto-fix common issues (creates backup)')
    parser.add_argument('--strict', action='store_true',
                        help='Enable strict mode (treats warnings as errors)')
    parser.add_argument('--output', choices=['cli', 'json'], default='cli',
                        help='Output format (default: cli)')
    parser.add_argument('--no-color', action='store_true',
                        help='Disable colored output')
    
    args = parser.parse_args()
    
    # Disable colors if requested
    if args.no_color:
        Colors.disable()
    
    # Run validation
    validator = OpenClawValidator(strict=args.strict)
    result = validator.validate(args.config)
    
    # Apply fixes if requested
    if args.fix and result.to_dict()['summary']['errors'] == 0:
        if validator.apply_fixes(args.config):
            # Re-validate after fixes
            validator = OpenClawValidator(strict=args.strict)
            result = validator.validate(args.config)
    
    # Print results
    print_results(result, args.output)
    
    # Exit with appropriate code
    sys.exit(0 if not result.has_errors() else 1)


if __name__ == '__main__':
    main()
