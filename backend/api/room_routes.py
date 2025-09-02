from flask import Blueprint

bp = Blueprint('room', __name__)

@bp.route('/test')
def test():
    return {'message': 'Room API working'}