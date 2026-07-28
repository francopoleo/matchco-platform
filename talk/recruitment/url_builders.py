"""
Utilities for building recruitment signup URLs with optional UTM tracking parameters.

Supports both:
1. Simple URLs: No tracking (for physical locations)
2. Rich URLs: With UTM parameters (for campaigns)
"""

from urllib.parse import urlencode, parse_qs, urlparse, urlunparse
from typing import Optional, Dict, Any


class URLBuilder:
    """Build recruitment signup URLs with optional UTM parameters."""

    # Standard UTM parameter names (Google Analytics convention)
    UTM_PARAMS = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'}

    @staticmethod
    def add_utm_params(
        base_url: str,
        utm_source: Optional[str] = None,
        utm_medium: Optional[str] = None,
        utm_campaign: Optional[str] = None,
        utm_content: Optional[str] = None,
        utm_term: Optional[str] = None,
        qr_id: Optional[str] = None,
        **extra_params
    ) -> str:
        """
        Add UTM/tracking parameters to a URL.

        Args:
            base_url: Base URL (e.g., "https://example.com/signup/?org=acme")
            utm_source: Channel (email, flyer, social, job_fair, billboard, referral)
            utm_medium: Medium type (newsletter, event, print, social_media, etc)
            utm_campaign: Campaign name (recruitment_jul2026, etc)
            utm_content: Content variation (store_5, booth_3, etc)
            utm_term: Additional term (optional)
            qr_id: Unique QR code variant ID (email_jul_store5_001, etc)
            **extra_params: Any additional tracking parameters

        Returns:
            URL with parameters appended (query string safe)

        Example:
            >>> base = "https://example.com/signup/?org=acme"
            >>> url = URLBuilder.add_utm_params(
            ...     base,
            ...     utm_source='email',
            ...     utm_medium='newsletter',
            ...     utm_campaign='recruitment_jul2026',
            ...     qr_id='email_jul_store5_001'
            ... )
            >>> print(url)
            https://example.com/signup/?org=acme&utm_source=email&utm_medium=newsletter...
        """

        # Build params dict, only including non-None values
        params = {}

        if utm_source:
            params['utm_source'] = str(utm_source).lower()
        if utm_medium:
            params['utm_medium'] = str(utm_medium).lower()
        if utm_campaign:
            params['utm_campaign'] = str(utm_campaign).lower()
        if utm_content:
            params['utm_content'] = str(utm_content).lower()
        if utm_term:
            params['utm_term'] = str(utm_term).lower()
        if qr_id:
            params['qr_id'] = str(qr_id).lower()

        # Add any extra tracking params
        for key, value in extra_params.items():
            if value is not None and key not in URLBuilder.UTM_PARAMS:
                params[key] = str(value).lower()

        # Parse URL and append params
        if not params:
            # No params to add, return original URL
            return base_url

        # Use urllib to safely handle URL encoding
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query, keep_blank_values=True)

        # Flatten lists back to strings (parse_qs returns lists)
        for key in query_params:
            query_params[key] = query_params[key][0] if query_params[key] else ''

        # Merge new params (new params override existing ones)
        query_params.update(params)

        # Rebuild query string
        new_query = urlencode(query_params, safe='')
        new_parsed = parsed._replace(query=new_query)

        return urlunparse(new_parsed)

    @staticmethod
    def build_campaign_url(
        base_url: str,
        campaign_name: str,
        channel: str,
        store_id: Optional[int] = None,
        store_name: Optional[str] = None,
        content: Optional[str] = None,
        qr_variant: Optional[str] = None,
    ) -> str:
        """
        Build a campaign-tracked signup URL using standard campaign naming convention.

        Uses pattern: {channel}_{descriptor}_{optional_extra}

        Args:
            base_url: Base signup URL
            campaign_name: Campaign identifier (e.g., "email_newsletter_jul2026", "flyer_bourbon_store5")
            channel: Channel type ("email", "flyer", "social", "job_fair", "billboard", "referral")
            store_id: Optional store ID
            store_name: Optional store name/identifier
            content: Optional content/variation identifier
            qr_variant: Optional specific QR variant ID

        Returns:
            Full URL with campaign UTM parameters

        Example:
            >>> URLBuilder.build_campaign_url(
            ...     "https://example.com/signup/?org=acme",
            ...     campaign_name="email_newsletter_jul2026",
            ...     channel="email",
            ...     store_id=5,
            ...     qr_variant="email_jul_store5_001"
            ... )
            https://example.com/signup/?org=acme&utm_source=email&utm_medium=newsletter...
        """

        # Map channel to utm_source and utm_medium
        channel_config = {
            'email': {'utm_source': 'email', 'utm_medium': 'email_campaign'},
            'social': {'utm_source': 'social_media', 'utm_medium': 'social_media'},
            'flyer': {'utm_source': 'flyer', 'utm_medium': 'print'},
            'billboard': {'utm_source': 'billboard', 'utm_medium': 'outdoor_advertising'},
            'job_fair': {'utm_source': 'job_fair', 'utm_medium': 'event'},
            'referral': {'utm_source': 'referral', 'utm_medium': 'referral_program'},
            'event': {'utm_source': 'event', 'utm_medium': 'event'},
            'direct': {'utm_source': 'direct', 'utm_medium': 'direct'},
        }

        utm_config = channel_config.get(channel.lower(), {
            'utm_source': channel.lower(),
            'utm_medium': channel.lower(),
        })

        # Build content identifier
        utm_content = content
        if store_name and not content:
            utm_content = store_name.lower().replace(' ', '_')
        elif store_id and not content and not store_name:
            utm_content = f'store_{store_id}'

        return URLBuilder.add_utm_params(
            base_url,
            utm_source=utm_config['utm_source'],
            utm_medium=utm_config['utm_medium'],
            utm_campaign=campaign_name,
            utm_content=utm_content,
            qr_id=qr_variant,
        )

    @staticmethod
    def validate_utm_params(
        utm_source: Optional[str] = None,
        utm_medium: Optional[str] = None,
        utm_campaign: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Validate UTM parameters for common issues.

        Returns:
            (is_valid, error_message)
        """

        if utm_campaign and len(utm_campaign) > 120:
            return False, "utm_campaign too long (max 120 chars)"

        if utm_source and ' ' in utm_source:
            return False, "utm_source cannot contain spaces (use underscores)"

        if utm_medium and ' ' in utm_medium:
            return False, "utm_medium cannot contain spaces (use underscores)"

        return True, ""

    @staticmethod
    def extract_utm_params(url: str) -> Dict[str, str]:
        """
        Extract all UTM parameters from a URL.

        Returns:
            Dict of {param_name: value} for all utm_* and qr_id params found
        """

        parsed = urlparse(url)
        query_params = parse_qs(parsed.query, keep_blank_values=True)

        utm_params = {}
        for param in URLBuilder.UTM_PARAMS | {'qr_id'}:
            if param in query_params:
                utm_params[param] = query_params[param][0]

        return utm_params
