# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: proof markup. On the approval page a client clicks on an image
# to pin numbered notes. Each marked image is saved on the work item as an
# attachment with the numbered pins drawn on it, and the notes are added as a
# comment. Marked copies are never sent as proofs (see proof_files).

import io
import json
import uuid
from html import escape

from PIL import Image, ImageDraw, ImageFont

from plane.db.models import FileAsset
from plane.settings.storage import S3Storage

MAX_MARKS = 30
MAX_TEXT = 500
PIN = (220, 38, 38)


def parse_marks(raw, allowed_assets):
    """[{asset, x, y, text}] from the page, kept only for this request's images."""
    try:
        marks = json.loads(raw or "[]")
    except ValueError:
        return []
    cleaned = []
    for mark in marks if isinstance(marks, list) else []:
        if not isinstance(mark, dict) or str(mark.get("asset")) not in allowed_assets:
            continue
        try:
            x = min(max(float(mark.get("x")), 0.0), 100.0)
            y = min(max(float(mark.get("y")), 0.0), 100.0)
        except (TypeError, ValueError):
            continue
        cleaned.append({"asset": str(mark["asset"]), "x": x, "y": y, "text": str(mark.get("text") or "")[:MAX_TEXT].strip()})
    return cleaned[:MAX_MARKS]


def _font(size):
    for name in ("DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_pins(data, marks):
    image = Image.open(io.BytesIO(data))
    image = image.convert("RGB")
    width, height = image.size
    draw = ImageDraw.Draw(image)
    radius = max(12, min(width, height) // 40)
    font = _font(int(radius * 1.2))
    for number, mark in enumerate(marks, start=1):
        cx, cy = mark["x"] / 100 * width, mark["y"] / 100 * height
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=PIN, outline=(255, 255, 255), width=max(2, radius // 5),
        )
        draw.text((cx, cy), str(number), fill=(255, 255, 255), font=font, anchor="mm")
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def save_markup(marks, assets_by_id, actor_id, who, add_comment):
    """Per marked image: attach the pinned copy to its work item and comment the notes."""
    storage = S3Storage()
    by_asset = {}
    for mark in marks:
        by_asset.setdefault(mark["asset"], []).append(mark)
    for asset_id, asset_marks in by_asset.items():
        asset = assets_by_id[asset_id]
        name = asset.attributes.get("name") or "image"
        copy_name = f"Σημειώσεις πελάτη – {name.rsplit('.', 1)[0]}.png"
        try:
            original = storage.s3_client.get_object(Bucket=storage.aws_storage_bucket_name, Key=asset.asset.name)
            png = draw_pins(original["Body"].read(), asset_marks)
            key = f"{asset.workspace_id}/{uuid.uuid4().hex}-markup.png"
            storage.s3_client.put_object(
                Bucket=storage.aws_storage_bucket_name, Key=key, Body=png, ContentType="image/png"
            )
            FileAsset.objects.create(
                asset=key,
                attributes={"name": copy_name, "type": "image/png", "size": len(png), "gam_markup": True},
                size=len(png),
                workspace_id=asset.workspace_id,
                project_id=asset.project_id,
                issue_id=asset.issue_id,
                entity_type=FileAsset.EntityTypeContext.ISSUE_ATTACHMENT,
                is_uploaded=True,
            )
            attached = f" Δείτε το συνημμένο «{escape(copy_name)}»."
        except Exception:
            attached = ""
        items = "".join(
            f"<li>{escape(mark['text']) or '<em>(χωρίς κείμενο)</em>'}</li>" for mark in asset_marks
        )
        add_comment(
            asset.issue,
            actor_id,
            f"<p>📍 Σημειώσεις πελάτη ({escape(who)}) πάνω στο «{escape(name)}».{attached}</p><ol>{items}</ol>",
        )
