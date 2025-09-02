from flask import Blueprint

bp = Blueprint('question', __name__)

@bp.route('/test')
def test():
    return {'message': 'Question API working'}