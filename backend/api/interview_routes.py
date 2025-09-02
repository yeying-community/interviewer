from flask import Blueprint

bp = Blueprint('interview', __name__)

@bp.route('/test')
def test():
    return {'message': 'Interview API working'}