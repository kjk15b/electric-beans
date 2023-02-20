from flask import Flask, render_template, request, make_response
from utils.electric_helper import Electric_Helper

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def main_route():
    '''
    Main route that handles most activity
    Will generate a dummy graph on GET and a user filled graph on POST
    '''
    options = {
        'charge_type' : [
            'hline',
            'vline',
        ],
        'lengths' : [
            '1',
            '2',
            '3',
            '4',
            'inf'
        ]
    }
    eh = Electric_Helper(cmap='hot')
    my_fig = None
    if request.method == 'POST':
        csv_file = request.files['csv_file']
        eh.parse_csv_file(csv_file)
        my_fig = eh.generate_figure()
    else:
        eh.sum_vectors(1, 0, 0)
        my_fig = eh.generate_figure()
    return render_template('index.html', method=request.method, figure=my_fig, options=options)

@app.route('/api/get/csv/line', methods=['POST'])
def get_csv_line_route():
    eh = Electric_Helper()
    results = request.form.to_dict()
    
    content = eh.generate_csv_line(
            charge_type=results['charge_type'],
            length=results['length'],
            xi=results['xi'],
            yi=results['yi'],
            qi=results['qi'])
    
    response = make_response(
        content.getvalue()
        )
    response.headers['Content-Disposition'] = 'attachment; filename={}.csv'.format(results['charge_type'])
    response.mimetype = 'text/csv'
    return response

@app.route('/api/get/csv/circle', methods=['POST'])
def get_csv_circle_route():
    eh = Electric_Helper()
    results = request.form.to_dict()
    
    content = eh.generate_csv_circle(
            ri=int(results['ri']),
            xi=int(results['xi']),
            yi=int(results['yi']),
            qi=results['qi'])
    
    response = make_response(
        content.getvalue()
        )
    response.headers['Content-Disposition'] = 'attachment; filename=circle.csv'
    response.mimetype = 'text/csv'
    return response


if __name__ == '__main__':
    app.run(port=8080, debug=True)