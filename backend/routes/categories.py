from flask import Blueprint, jsonify, request
from mongoengine.queryset.visitor import Q

from backend.middleware.auth import require_admin
from backend.models import Category, Movie
from backend.utils.mongo import parse_object_id

bp = Blueprint("categories", __name__, url_prefix="/api/categories")


@bp.get("/")
def list_categories():
    items = Category.objects.order_by("name")
    return jsonify(
        {
            "items": [
                {
                    "_id": str(c.id),
                    "name": c.name,
                    "displayName": c.display_name,
                    "movieIds": [
                        str(m.id) for m in Movie.objects(category_ids=c.id).only("id")
                    ],
                }
                for c in items
            ]
        }
    )


@bp.post("/")
@require_admin
def create_category():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    if Category.objects(name__iexact=name).first():
        return jsonify({"error": f"Category already exists: {name}"}), 409
    display = str(data.get("displayName", "")).strip() or name
    cat = Category(name=name, display_name=display)
    cat.save()
    for mid in data.get("movieIds") or []:
        moid = parse_object_id(mid)
        movie = Movie.objects(id=moid).first() if moid else None
        if movie and cat.id not in (movie.category_ids or []):
            movie.category_ids = list(movie.category_ids or []) + [cat.id]
            movie.save()
    return jsonify({"category": {"id": str(cat.id), "name": cat.name}}), 201


@bp.put("/<category_id>")
@require_admin
def update_category(category_id: str):
    cid = parse_object_id(category_id)
    if not cid:
        return jsonify({"error": "categoryId không hợp lệ"}), 400
    cat = Category.objects(id=cid).first()
    if not cat:
        return jsonify({"error": "Không tìm thấy"}), 404
    data = request.get_json(silent=True) or {}
    if "name" in data:
        name = str(data["name"]).strip()
        if name:
            exists = Category.objects(Q(name__iexact=name) & Q(id__ne=cat.id)).first()
            if exists:
                return jsonify({"error": "Tên category đã tồn tại"}), 409
            cat.name = name
    if "displayName" in data:
        cat.display_name = str(data["displayName"]).strip() or cat.name
    if "movieIds" in data:
        new_movie_ids = []
        for mid in data.get("movieIds") or []:
            moid = parse_object_id(mid)
            if moid and Movie.objects(id=moid).first():
                new_movie_ids.append(moid)
        for movie in Movie.objects(category_ids=cat.id):
            ids = [x for x in (movie.category_ids or []) if x != cat.id]
            if movie.id in new_movie_ids:
                if cat.id not in ids:
                    ids.append(cat.id)
            movie.category_ids = ids
            movie.save()
        for moid in new_movie_ids:
            movie = Movie.objects(id=moid).first()
            if movie and cat.id not in (movie.category_ids or []):
                movie.category_ids = list(movie.category_ids or []) + [cat.id]
                movie.save()
    cat.save()
    return jsonify({"category": {"id": str(cat.id), "name": cat.name}})


@bp.delete("/<category_id>")
@require_admin
def delete_category(category_id: str):
    cid = parse_object_id(category_id)
    if not cid:
        return jsonify({"error": "categoryId không hợp lệ"}), 400
    cat = Category.objects(id=cid).first()
    if not cat:
        return jsonify({"error": "Không tìm thấy"}), 404
    for movie in Movie.objects(category_ids=cat.id):
        movie.category_ids = [x for x in (movie.category_ids or []) if x != cat.id]
        movie.save()
    cat.delete()
    return jsonify({"ok": True})
