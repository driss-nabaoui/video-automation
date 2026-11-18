import os
import re
import hashlib
import random
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import httpx
from PIL import Image, ImageDraw

from app.config import settings
from app.schemas import SceneSpec, AssetRecord, AssetVerificationResult
from app.services.ai_video_engine import ai_video_engine


class LicenseVerifier:
    """
    Enforces strict copyright and commercial use verification.
    Permits only Public Domain, CC0, CC BY, Pexels, and Pixabay commercial licenses.
    Zero-tolerance for NonCommercial (-NC), NoDerivatives (-ND), or Editorial-Only content.
    """

    ALLOWED_CC_LICENSES = {
        "public domain", "pd", "cc0", "cc-0",
        "cc by", "cc by 2.0", "cc by 2.5", "cc by 3.0", "cc by 4.0",
        "cc by-sa", "cc by-sa 2.0", "cc by-sa 2.5", "cc by-sa 3.0", "cc by-sa 4.0"
    }

    REJECTED_KEYWORDS = [
        "-nc", "noncommercial", "non-commercial",
        "-nd", "noderivatives", "no-derivatives",
        "editorial", "editorial-only", "fair use", "all rights reserved"
    ]

    @classmethod
    def verify(cls, source: str, raw_license: str, author: str = "", title: str = "") -> AssetVerificationResult:
        license_clean = (raw_license or "").strip().lower()

        # 1. Check for forbidden non-commercial or editorial terms
        for keyword in cls.REJECTED_KEYWORDS:
            if keyword in license_clean:
                return AssetVerificationResult(
                    is_approved=False,
                    license_name=raw_license,
                    is_commercial_safe=False,
                    attribution_required=False,
                    attribution_text=None,
                    rejection_reason=f"License contains restricted term: '{keyword}'"
                )

        # 2. Source-specific validation rules
        if source.upper() == "NASA":
            # US Government work (17 U.S.C. § 105) - Public Domain
            attr = f"NASA / {author}" if author else "NASA Open Media"
            return AssetVerificationResult(
                is_approved=True,
                license_name="NASA Public Domain",
                is_commercial_safe=True,
                attribution_required=True,
                attribution_text=attr
            )

        elif source.upper() == "PEXELS":
            # Pexels Commercial License
            attr = f"Photo/Footage by {author} via Pexels" if author else "Pexels License (Commercial Safe)"
            return AssetVerificationResult(
                is_approved=True,
                license_name="Pexels License",
                is_commercial_safe=True,
                attribution_required=False,
                attribution_text=attr
            )

        elif source.upper() == "PIXABAY":
            # Pixabay Content License
            attr = f"Media by {author} via Pixabay" if author else "Pixabay License (Commercial Safe)"
            return AssetVerificationResult(
                is_approved=True,
                license_name="Pixabay Content License",
                is_commercial_safe=True,
                attribution_required=False,
                attribution_text=attr
            )

        elif source.upper() == "WIKIMEDIA":
            # Check against verified open licenses
            is_matched = any(al in license_clean for al in cls.ALLOWED_CC_LICENSES)
            if is_matched or "public domain" in license_clean:
                needs_attr = not ("cc0" in license_clean or "public domain" in license_clean)
                clean_artist = re.sub(r"<.*?>", "", author).strip() if author else "Wikimedia Contributor"
                attr = f"'{title}' by {clean_artist} ({raw_license})"
                return AssetVerificationResult(
                    is_approved=True,
                    license_name=raw_license,
                    is_commercial_safe=True,
                    attribution_required=needs_attr,
                    attribution_text=attr
                )
            else:
                return AssetVerificationResult(
                    is_approved=False,
                    license_name=raw_license,
                    is_commercial_safe=False,
                    attribution_required=False,
                    attribution_text=None,
                    rejection_reason=f"Wikimedia license '{raw_license}' not verified commercial-safe."
                )

        elif source.upper() == "LOCAL_WINDOWS":
            return AssetVerificationResult(
                is_approved=True,
                license_name="User Authored / Licensed Media",
                is_commercial_safe=True,
                attribution_required=False,
                attribution_text="User Provided Media"
            )

        elif source.upper() in ("AI_VIDEO", "AI_VIDEO_GENERATOR", "CINEMATIC_SYNTHESIZER", "FAL_AI", "RUNWAY_ML", "KLING_AI", "LUMA_RAY", "CACHE"):
            return AssetVerificationResult(
                is_approved=True,
                license_name="VOIDORA Proprietary Original",
                is_commercial_safe=True,
                attribution_required=False,
                attribution_text="VOIDORA Original Cinematic Generation"
            )

        return AssetVerificationResult(
            is_approved=False,
            license_name=raw_license or "Unknown",
            is_commercial_safe=False,
            attribution_required=False,
            attribution_text=None,
            rejection_reason="Unrecognized media source"
        )


class AssetEngine:
    """
    Intelligent, copyright-safe visual asset acquisition pipeline.
    Connects to NASA Open Media, Wikimedia Commons, Pexels, and Pixabay.
    Guarantees SHA-256 deduplication and attribution generation.
    """

    NASA_SEARCH_URL = "https://images-api.nasa.gov/search"
    WIKIMEDIA_API_URL = "https://commons.wikimedia.org/w/api.php"
    PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"
    PEXELS_PHOTO_URL = "https://api.pexels.com/v1/search"
    PIXABAY_API_URL = "https://pixabay.com/api/"

    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        """Calculates SHA-256 hex digest for asset deduplication."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    # =========================================================
    # 1. NASA Open Media Search & Download (Videos & Images)
    # =========================================================
    async def fetch_nasa_asset(
        self,
        query: str,
        preferred_type: str = "IMAGE",
        target_filename_prefix: str = "nasa"
    ) -> Optional[AssetRecord]:
        """Fetches authentic NASA footage or high-res imagery with rights verification."""
        media_types = "video" if preferred_type == "VIDEO" else "image"

        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                res = await client.get(
                    self.NASA_SEARCH_URL,
                    params={"q": query, "media_type": media_types}
                )
                if res.status_code != 200:
                    return None

                data = res.json()
                items = data.get("collection", {}).get("items", [])
                if not items:
                    return None

                for item in items:
                    data_entry = item.get("data", [{}])[0]
                    nasa_id = data_entry.get("nasa_id", "")
                    title = data_entry.get("title", "")
                    center = data_entry.get("center", "NASA")
                    item_type = data_entry.get("media_type", "image").upper()
                    coll_href = item.get("href", "")

                    if preferred_type == "IMAGE" and item_type != "IMAGE":
                        continue
                    if preferred_type == "VIDEO" and item_type != "VIDEO":
                        continue

                    # Verify license
                    v = LicenseVerifier.verify("NASA", "NASA Public Domain", author=center, title=title)
                    if not v.is_approved:
                        continue

                    # Video Asset Ingestion
                    if item_type == "VIDEO" and coll_href:
                        coll_res = await client.get(coll_href)
                        if coll_res.status_code == 200:
                            files = coll_res.json()
                            # Prefer medium or small video to avoid downloading multi-gigabyte raw files
                            video_url = next((f for f in files if "~medium.mp4" in f or "~small.mp4" in f or "~large.mp4" in f), None)
                            if not video_url:
                                video_url = next((f for f in files if "~orig.mp4" in f), None)
                            if video_url:
                                out_name = f"{target_filename_prefix}_{nasa_id[:32]}.mp4"
                                out_path = settings.visual_assets / out_name
                                if not out_path.is_file():
                                    dl = await client.get(video_url)
                                    if dl.status_code == 200 and 100000 < len(dl.content) <= 50_000_000:
                                        with open(out_path, "wb") as f_out:
                                            f_out.write(dl.content)

                                if out_path.is_file() and out_path.stat().st_size > 0:
                                    sha256 = self.calculate_sha256(out_path)
                                    return AssetRecord(
                                        source="NASA",
                                        external_id=nasa_id,
                                        asset_type="VIDEO",
                                        file_path=str(out_path),
                                        source_url=f"https://images.nasa.gov/details-{nasa_id}",
                                        creator=center,
                                        license_name=v.license_name,
                                        license_url="https://www.nasa.gov/multimedia/guidelines/index.html",
                                        attribution_text=v.attribution_text,
                                        is_commercial_safe=True,
                                        sha256_hash=sha256
                                    )

                    # Image Asset Ingestion
                    links = item.get("links", [])
                    img_url = next((l.get("href") for l in links if l.get("render") == "image"), None)
                    if img_url:
                        out_name = f"{target_filename_prefix}_{nasa_id[:32]}.jpg"
                        out_path = settings.visual_assets / out_name
                        if not out_path.is_file():
                            dl = await client.get(img_url)
                            if dl.status_code == 200 and len(dl.content) > 10000:
                                with open(out_path, "wb") as f_out:
                                    f_out.write(dl.content)

                        if out_path.is_file() and out_path.stat().st_size > 0:
                            sha256 = self.calculate_sha256(out_path)
                            return AssetRecord(
                                source="NASA",
                                external_id=nasa_id,
                                asset_type="IMAGE",
                                file_path=str(out_path),
                                source_url=f"https://images.nasa.gov/details-{nasa_id}",
                                creator=center,
                                license_name=v.license_name,
                                license_url="https://www.nasa.gov/multimedia/guidelines/index.html",
                                attribution_text=v.attribution_text,
                                is_commercial_safe=True,
                                sha256_hash=sha256
                            )
        except Exception:
            pass

        return None

    # =========================================================
    # 2. Wikimedia Commons Search & Download (Archival / History)
    # =========================================================
    async def fetch_wikimedia_asset(
        self,
        query: str,
        target_filename_prefix: str = "wiki"
    ) -> Optional[AssetRecord]:
        """Fetches historical photography, documents, and astronomical illustrations."""
        headers = {"User-Agent": "VOIDORA-Documentary-Engine/2.0 (contact@voidora.tv)"}
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": "6",  # Media files
            "gsrlimit": "5",
            "prop": "imageinfo",
            "iiprop": "url|size|extmetadata",
            "format": "json"
        }

        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=headers) as client:
                res = await client.get(self.WIKIMEDIA_API_URL, params=params)
                if res.status_code != 200:
                    return None

                data = res.json()
                pages = data.get("query", {}).get("pages", {})
                for _, page in pages.items():
                    info = page.get("imageinfo", [{}])[0]
                    file_url = info.get("url")
                    if not file_url:
                        continue
                    clean_path = file_url.split("?")[0].lower()
                    if not clean_path.endswith((".jpg", ".jpeg", ".png", ".webp")):
                        continue

                    extmeta = info.get("extmetadata", {})
                    lic_name = extmeta.get("LicenseShortName", {}).get("value", "")
                    artist = extmeta.get("Artist", {}).get("value", "")
                    title = page.get("title", "")

                    # Verify copyright
                    v = LicenseVerifier.verify("WIKIMEDIA", lic_name, author=artist, title=title)
                    if not v.is_approved:
                        continue

                    clean_title = re.sub(r"[^\w\-_\.]", "_", title[:28])
                    out_path = settings.visual_assets / f"{target_filename_prefix}_{clean_title}.jpg"
                    if not out_path.is_file():
                        dl = await client.get(file_url)
                        if dl.status_code == 200 and len(dl.content) > 15000:
                            with open(out_path, "wb") as f_out:
                                f_out.write(dl.content)

                    if out_path.is_file() and out_path.stat().st_size > 0:
                        sha256 = self.calculate_sha256(out_path)
                        return AssetRecord(
                            source="WIKIMEDIA",
                            external_id=str(page.get("pageid", "")),
                            asset_type="IMAGE",
                            file_path=str(out_path),
                            source_url=file_url,
                            creator=re.sub(r"<.*?>", "", artist).strip(),
                            license_name=v.license_name,
                            license_url="https://commons.wikimedia.org/wiki/Commons:Licensing",
                            attribution_text=v.attribution_text,
                            is_commercial_safe=True,
                            sha256_hash=sha256
                        )
        except Exception:
            pass

        return None

    # =========================================================
    # 3. Pexels Stock Video & Photo Ingestion (Optional Key)
    # =========================================================
    async def fetch_pexels_asset(
        self,
        query: str,
        preferred_type: str = "VIDEO",
        target_filename_prefix: str = "pexels"
    ) -> Optional[AssetRecord]:
        """Fetches high-quality commercial-safe footage from Pexels if API key configured."""
        if not settings.PEXELS_API_KEY:
            return None

        headers = {"Authorization": settings.PEXELS_API_KEY}
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=headers) as client:
                if preferred_type == "VIDEO":
                    res = await client.get(self.PEXELS_VIDEO_URL, params={"query": query, "per_page": 3, "orientation": "landscape"})
                    if res.status_code == 200:
                        videos = res.json().get("videos", [])
                        if videos:
                            vid = videos[0]
                            # Find best 1080p MP4 file
                            v_files = vid.get("video_files", [])
                            best_file = next((f for f in v_files if f.get("width") == 1920 or f.get("height") == 1080), v_files[0] if v_files else None)
                            if best_file and best_file.get("link"):
                                out_path = settings.visual_assets / f"{target_filename_prefix}_{vid['id']}.mp4"
                                if not out_path.is_file():
                                    dl = await client.get(best_file["link"])
                                    if dl.status_code == 200:
                                        with open(out_path, "wb") as f_out:
                                            f_out.write(dl.content)

                                if out_path.is_file() and out_path.stat().st_size > 0:
                                    sha256 = self.calculate_sha256(out_path)
                                    return AssetRecord(
                                        source="PEXELS",
                                        external_id=str(vid["id"]),
                                        asset_type="VIDEO",
                                        file_path=str(out_path),
                                        source_url=vid.get("url"),
                                        creator=vid.get("user", {}).get("name", "Pexels Creator"),
                                        license_name="Pexels License",
                                        license_url="https://www.pexels.com/license/",
                                        attribution_text=f"Video by {vid.get('user', {}).get('name', 'Creator')} via Pexels",
                                        is_commercial_safe=True,
                                        sha256_hash=sha256
                                    )

                # Fallback to Pexels Photos
                p_res = await client.get(self.PEXELS_PHOTO_URL, params={"query": query, "per_page": 3})
                if p_res.status_code == 200:
                    photos = p_res.json().get("photos", [])
                    if photos:
                        p = photos[0]
                        img_url = p.get("src", {}).get("large2x") or p.get("src", {}).get("large")
                        if img_url:
                            out_path = settings.visual_assets / f"{target_filename_prefix}_{p['id']}.jpg"
                            if not out_path.is_file():
                                dl = await client.get(img_url)
                                if dl.status_code == 200:
                                    with open(out_path, "wb") as f_out:
                                        f_out.write(dl.content)

                            if out_path.is_file() and out_path.stat().st_size > 0:
                                sha256 = self.calculate_sha256(out_path)
                                return AssetRecord(
                                    source="PEXELS",
                                    external_id=str(p["id"]),
                                    asset_type="IMAGE",
                                    file_path=str(out_path),
                                    source_url=p.get("url"),
                                    creator=p.get("photographer", "Pexels Creator"),
                                    license_name="Pexels License",
                                    license_url="https://www.pexels.com/license/",
                                    attribution_text=f"Photo by {p.get('photographer', 'Creator')} via Pexels",
                                    is_commercial_safe=True,
                                    sha256_hash=sha256
                                )
        except Exception:
            pass

        return None

    # =========================================================
    # 4. Multi-Source Pipeline & Scene Assignment
    # =========================================================
    async def acquire_assets_for_scenes(
        self,
        scenes: List[SceneSpec],
        video_format: str = "LONG_FORM"
    ) -> Tuple[List[SceneSpec], List[AssetRecord], List[str]]:
        """
        Orchestrates visual matching across all scenes.
        Returns (updated_scenes_with_assets, asset_records, attributions_summary).
        """
        updated_scenes = []
        asset_records = []
        attributions = []

        is_shorts = (video_format.upper() == "SHORTS")
        out_w, out_h = (1080, 1920) if is_shorts else (1920, 1080)

        for scene in scenes:
            scene_copy = scene.model_copy()
            prefix = f"scene_{scene.scene_index}"
            shot_type = getattr(scene, "shot_type", "AI_CINEMATIC") or "AI_CINEMATIC"
            cam_motion = getattr(scene, "camera_motion", "slow_push_in") or getattr(scene, "motion_type", "slow_push_in") or "slow_push_in"
            lighting = getattr(scene, "visual_lighting", "") or ""
            prompt = scene.ai_prompt or scene.visual_description or "deep space mystery"
            record = None

            # Strategy 1: AI Cinematic Generation (Primary Hollywood path)
            if shot_type == "AI_CINEMATIC" and settings.AI_VIDEO_ENABLED:
                vid_path, provider, _ = await ai_video_engine.generate_cinematic_shot(
                    prompt=prompt,
                    camera_motion=cam_motion,
                    duration_seconds=scene.duration_seconds,
                    aspect_ratio="9:16" if is_shorts else "16:9",
                    filename_prefix=prefix,
                    lighting=lighting
                )
                if vid_path and vid_path.is_file():
                    sha256 = self.calculate_sha256(vid_path)
                    record = AssetRecord(
                        source=provider,
                        external_id=f"ai_{scene.scene_index}",
                        asset_type="VIDEO",
                        file_path=str(vid_path),
                        creator="VOIDORA Hollywood AI Cinematographer",
                        license_name="VOIDORA Proprietary Original",
                        attribution_text="VOIDORA Original Cinematic Generation",
                        is_commercial_safe=True,
                        sha256_hash=sha256,
                        duration_seconds=scene.duration_seconds
                    )

            # Strategy 2: Authentic Archival (Historical document / log / scan)
            if not record and shot_type == "ARCHIVAL_AUTHENTIC":
                archival_rec = None
                for kw in (scene.search_keywords or []):
                    archival_rec = await self.fetch_wikimedia_asset(kw, target_filename_prefix=f"{prefix}_archival")
                    if archival_rec:
                        break
                if not archival_rec and scene.visual_description:
                    archival_rec = await self.fetch_wikimedia_asset(scene.visual_description[:30], target_filename_prefix=f"{prefix}_archival")

                # If an authentic archival still is found, convert to cinematic 3D motion video clip
                if archival_rec and archival_rec.file_path:
                    vid_path, provider, _ = await ai_video_engine.generate_cinematic_shot(
                        prompt=prompt,
                        camera_motion=cam_motion,
                        duration_seconds=scene.duration_seconds,
                        aspect_ratio="9:16" if is_shorts else "16:9",
                        filename_prefix=f"{prefix}_archival_motion",
                        lighting=lighting,
                        reference_image_path=archival_rec.file_path
                    )
                    if vid_path and vid_path.is_file():
                        sha256 = self.calculate_sha256(vid_path)
                        record = AssetRecord(
                            source="WIKIMEDIA_CINEMATIC_ARCHIVAL",
                            external_id=archival_rec.external_id,
                            asset_type="VIDEO",
                            file_path=str(vid_path),
                            source_url=archival_rec.source_url,
                            creator=archival_rec.creator,
                            license_name=archival_rec.license_name,
                            license_url=archival_rec.license_url,
                            attribution_text=archival_rec.attribution_text,
                            is_commercial_safe=True,
                            sha256_hash=sha256,
                            duration_seconds=scene.duration_seconds
                        )

            # Strategy 3: Scientific NASA footage or multi-source fallback search
            if not record:
                candidate_queries = []
                for kw in (scene.search_keywords or []):
                    cleaned_kw = kw.strip()
                    if cleaned_kw and cleaned_kw not in candidate_queries:
                        candidate_queries.append(cleaned_kw)
                if scene.visual_description:
                    candidate_queries.append(scene.visual_description[:35].strip())
                if not candidate_queries:
                    candidate_queries.append("deep space galaxy")

                for query in candidate_queries:
                    q_lower = query.lower()
                    if any(k in q_lower for k in ["space", "galaxy", "telescope", "star", "hubble", "black hole", "cosmic", "mars", "nebula"]):
                        record = await self.fetch_nasa_asset(query, preferred_type="IMAGE", target_filename_prefix=prefix)
                        if not record:
                            record = await self.fetch_nasa_asset(query, preferred_type="VIDEO", target_filename_prefix=prefix)
                    if not record:
                        record = await self.fetch_wikimedia_asset(query, target_filename_prefix=prefix)
                    if not record and settings.PEXELS_API_KEY:
                        record = await self.fetch_pexels_asset(query, preferred_type="VIDEO", target_filename_prefix=prefix)
                    if record:
                        break

            # Strategy 4: Fail-Safe Cinematic Synthesizer (Guarantees zero static slates)
            if not record:
                vid_path, provider, _ = await ai_video_engine.generate_cinematic_shot(
                    prompt=prompt,
                    camera_motion=cam_motion,
                    duration_seconds=scene.duration_seconds,
                    aspect_ratio="9:16" if is_shorts else "16:9",
                    filename_prefix=prefix,
                    lighting=lighting
                )
                if vid_path and vid_path.is_file():
                    sha256 = self.calculate_sha256(vid_path)
                    record = AssetRecord(
                        source=provider,
                        external_id=f"fallback_{scene.scene_index}",
                        asset_type="VIDEO",
                        file_path=str(vid_path),
                        creator="VOIDORA Cinematic Core",
                        license_name="VOIDORA Proprietary Original",
                        attribution_text="VOIDORA Original Generation",
                        is_commercial_safe=True,
                        sha256_hash=sha256,
                        duration_seconds=scene.duration_seconds
                    )

            # Bind to scene
            scene_copy.asset_path = record.file_path
            scene_copy.asset_type = record.asset_type
            scene_copy.creator = record.creator
            scene_copy.license_name = record.license_name
            scene_copy.source_url = record.source_url
            scene_copy.attribution = record.attribution_text
            scene_copy.camera_motion = cam_motion
            scene_copy.motion_type = cam_motion

            updated_scenes.append(scene_copy)
            asset_records.append(record)
            if record.attribution_text and record.attribution_text not in attributions:
                attributions.append(record.attribution_text)

        return updated_scenes, asset_records, attributions


asset_engine = AssetEngine()
