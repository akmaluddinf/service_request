from flask import Flask, request, jsonify, json
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import datetime
from flask_cors import CORS, cross_origin



app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:123456@localhost:5432/project"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class EmployeeModel(db.Model):
    __tablename__ = 'employee'

    id = db.Column(db.Integer, primary_key=True)
    payroll = db.Column(db.Integer)
    name = db.Column(db.String())

    def __init__(self, payroll, name):
        self.payroll = payroll
        self.name = name

    def __repr__(self):
        return '<User %r>' % self.name

class ServiceModel(db.Model):
    __tablename__ = 'service'

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.String())
    service_type = db.Column(db.String())

    def __init__(self, service_id, service_type):
        self.service_id = service_id
        self.service_type = service_type

    def __repr__(self):
        return '<Service id %r>' % self.service_id

#===================================================================================        

class ServiceRequestModel(db.Model):
    __tablename__ = 'service_request'

    id = db.Column(db.Integer, primary_key=True)
    requester_name = db.Column(db.String())
    requester_payroll = db.Column(db.Integer)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    status = db.Column(db.String())
    estimated_total = db.Column(db.Numeric(10,2))
    service_items = db.relationship('ServiceItems', backref='service_request', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comments', backref='service_request', lazy=True, cascade="all, delete-orphan")

    def __init__(self, requester_name, requester_payroll, status, estimated_total):
        self.requester_name = requester_name
        self.requester_payroll = requester_payroll
        self.status = status
        self.estimated_total = estimated_total
        #self.created_date = created_date

    def __repr__(self):
        return '<User %r>' % self.requester_name

    def serialize(self):
        return{
            'service_request_id': self.id,
            'requester_name': self.requester_name,
            'requester_payroll': self.requester_payroll,
            'created_date': self.created_date,
            'status': self.status,
            'estimated_total': self.estimated_total,
            'service_items' : [{'service_item_id' : item.id, 'service_id' : item.service_id, 'service_type' : item.service_type, 'description' : item.description, 'quantity' : item.quantity, 'unit_price' : item.unit_price, 'service_request_id' : item.service_request_id} for item in self.service_items],
            'comments' : [{'comment_id' : item.id, 'requester_payroll' : item.user, 'comment' : item.comment, 'created_date' : item.created_date, 'service_request_id' : item.service_request_id} for item in self.comments]
        }


class ServiceItems(db.Model):
    __tablename__ = 'service_items'

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.String())
    service_type = db.Column(db.String())
    description = db.Column(db.String())
    quantity = db.Column(db.Integer)
    unit_price = db.Column(db.Numeric(10,2))
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'))


    def __init__(self, service_id, service_type, description, quantity, unit_price, service_request_id):
        self.service_id = service_id
        self.service_type = service_type
        self.description = description
        self.quantity = quantity
        self.unit_price = unit_price
        self.service_request_id = service_request_id

    def __repr__(self):
        return '<Service Id %r>' % self.service_id


class Comments(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer)
    comment = db.Column(db.String())
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'))


    def __init__(self, user, comment, service_request_id):
        self.user = user
        self.comment = comment
        self.service_request_id = service_request_id

    def __repr__(self):
        return '<Comment %r>' % self.comment

##########################################################################SERVICE REQUEST

@app.route('/')
@cross_origin(origin='*')
def hello():
	return 'Hello, World!'


@app.route('/service_request', methods=['POST', 'GET'])
@cross_origin(origin='*')
def service_request():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            new_service_request= ServiceRequestModel(
                requester_name=data['requester_name'], 
                requester_payroll=data['requester_payroll'],
                #created_date=data['created_date'],
                status = data['status'],
                estimated_total = data['estimated_total']
                )

            new_service_item= ServiceItems(
                service_request_id=data['service_request_id_svc'],
                service_id=data['service_id'], 
                service_type=data['service_type'],
                description = data['description'],
                quantity = data['quantity'],
                unit_price = data['unit_price'])

            new_comment= Comments(
                service_request_id=data['service_request_id_com'],
                user=data['user'], 
                comment=data['comment'])

            db.session.add(new_service_request)
            db.session.add(new_service_item)
            db.session.add(new_comment)
            db.session.commit()

            return {"message": f"Service Request with id: {new_service_request.id} has been created successfully."}
        else:
            return {"error": "The request payload is not in JSON format"}

    elif request.method == 'GET':
        service_requests = ServiceRequestModel.query.all()
        results = [
            {
                "id" : service_request.id,
                "requester_name" : service_request.requester_name,
                "requester_payroll" : service_request.requester_payroll,
                "created_date" : service_request.created_date,
                "status": service_request.status,
                "estimated_total": service_request.estimated_total

            } for service_request in service_requests]

        #return {"count": len(results), "service requests": results, "message": "success"}
        #return json.dumps({"count": len(results), "service requests": results, "message": "success"})
        return jsonify([service_request.serialize() for service_request in service_requests])

@app.route('/service_request/<id>', methods=['GET', 'PUT', 'DELETE'])
@cross_origin(origin='*')
def update_service_request(id):
    service_request = ServiceRequestModel.query.get_or_404(id)

    if request.method == 'GET':
        response = {
            "id" : service_request.id,
            "requester_name" : service_request.requester_name,
            "requester_payroll" : service_request.requester_payroll,
            "created_date" : service_request.created_date,
            "status": service_request.status,
            "estimated_total": service_request.estimated_total
        }
        return {"message": "success", "service request": response}

    elif request.method == 'PUT':
        data = request.get_json()

        service_request.requester_name=data['requester_name'], 
        service_request.requester_payroll=data['requester_payroll'],
        service_request.status = data['status'],
        service_request.estimated_total = data['estimated_total']

        db.session.add(service_request)
        db.session.commit()
        
        return {"message": f"service request id: {service_request.id} successfully updated"}

    elif request.method == 'DELETE':
        db.session.delete(service_request)
        db.session.commit()
        
        return {"message": f"service request id: {service_request.id} successfully deleted."}

#############################################################################SERVICE ITEMS

@app.route('/service_item', methods=['POST', 'GET'])
@cross_origin(origin='*')
def service_item():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            new_service_item= ServiceItems(
                service_request_id=data['service_request_id'],
                service_id=data['service_id'], 
                service_type=data['service_type'],
                description = data['description'],
                quantity = data['quantity'],
                unit_price = data['unit_price'])

            db.session.add(new_service_item)
            db.session.commit()

            return {"message": f"service item with service id: {new_service_item.service_id} has been created successfully."}
        else:
            return {"error": "The request payload is not in JSON format"}

    elif request.method == 'GET':
        service_items = ServiceItems.query.all()
        results = [
            {
                "service_request_id" : service_item.service_request_id,
                "id" : service_item.id,
                "service_id" : service_item.service_id,
                "service_type" : service_item.service_type,
                "description" : service_item.description,
                "quantity": service_item.quantity,
                "unit_price": service_item.unit_price

            } for service_item in service_items]

        return {"count": len(results), "service items": results, "message": "success"}


@app.route('/service_item/<id>', methods=['GET', 'PUT', 'DELETE'])
@cross_origin(origin='*')
def update_service_item(id):
    service_item = ServiceItems.query.get_or_404(id)

    if request.method == 'GET':
        response = {
            "service_request_id": service_item.service_request_id,
            "id" : service_item.id,
            "service_id" : service_item.service_id,
            "service_type" : service_item.service_type,
            "description" : service_item.description,
            "quantity": service_item.quantity,
            "unit_price": service_item.unit_price
        }
        return {"message": "success", "service item": response}

    elif request.method == 'PUT':
        data = request.get_json()

        service_item.service_request_id=data['service_request_id'], 
        service_item.service_id=data['service_id'], 
        service_item.service_type=data['service_type'],
        service_item.description = data['description'],
        service_item.quantity = data['quantity'],
        service_item.unit_price = data['unit_price']

        db.session.add(service_item)
        db.session.commit()
        
        return {"message": f"service item id: {service_item.id} successfully updated"}

    elif request.method == 'DELETE':
        db.session.delete(service_item)
        db.session.commit()
        
        return {"message": f"service item id: {service_item.id} successfully deleted."}


###############################################################################COMMENTS

@app.route('/comment', methods=['POST', 'GET'])
@cross_origin(origin='*')
def comment():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            new_comment= Comments(
                service_request_id=data['service_request_id'],
                user=data['user'], 
                comment=data['comment'])

            db.session.add(new_comment)
            db.session.commit()

            return {"message": f"comment with id: {new_comment.id} has been created successfully."}
        else:
            return {"error": "The request payload is not in JSON format"}

    elif request.method == 'GET':
        comments = Comments.query.all()
        results = [
            {
                "service_request_id": comment.service_request_id,
                "id" : comment.id,
                "user" : comment.user,
                "comment" : comment.comment,
                "created_date" : comment.created_date

            } for comment in comments]

        return {"count": len(results), "comments": results, "message": "success"}


@app.route('/comment/<id>', methods=['GET', 'PUT', 'DELETE'])
@cross_origin(origin='*')
def update_comment(id):
    comment = Comments.query.get_or_404(id)

    if request.method == 'GET':
        response = {
            "service_request_id": comment.service_request_id,
            "id" : comment.id,
            "user" : comment.user,
            "comment" : comment.comment,
            "created_date" : comment.created_date
        }
        return {"message": "success", "comment": response}

    elif request.method == 'PUT':
        data = request.get_json()

        comment.service_request_id=data['service_request_id'], 
        comment.user=data['user'],
        comment.comment = data['comment']

        db.session.add(comment)
        db.session.commit()
        
        return {"message": f"comment id: {comment.id} successfully updated"}

    elif request.method == 'DELETE':
        db.session.delete(comment)
        db.session.commit()
        
        return {"message": f"comment id: {comment.id} successfully deleted."}

#================================================================================EMPLOYEE
@app.route('/employee', methods=['POST', 'GET'])
@cross_origin(origin='*')
def handle_employee():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            new_employee = EmployeeModel(payroll=data['payroll'], name=data['name'])

            db.session.add(new_employee)
            db.session.commit()

            return {"message": f"employee {new_employee.name} has been created successfully."}
        else:
            return {"error": "The request payload is not in JSON format"}

    elif request.method == 'GET':
        employees = EmployeeModel.query.all()
        results = [
            {
                "payroll": employee.payroll,
                "name": employee.name
            } for employee in employees]

        return {"count": len(results), "employees": results, "message": "success"}


@app.route('/employee/<id>', methods=['GET', 'PUT', 'DELETE'])
@cross_origin(origin='*')
def update_employee(id):
    employee = EmployeeModel.query.get_or_404(id)

    if request.method == 'GET':
        response = {
            "payroll": employee.payroll,
            "name": employee.name
        }
        return {"message": "success", "employee": response}

    elif request.method == 'PUT':
        data = request.get_json()
        employee.payroll = data['payroll']
        employee.name = data['name']

        db.session.add(employee)
        db.session.commit()
        
        return {"message": f"employee {employee.name} successfully updated"}

    elif request.method == 'DELETE':
        db.session.delete(employee)
        db.session.commit()
        
        return {"message": f"Employee {employee.name} successfully deleted."}

#================================================================================SERVICE
@app.route('/service', methods=['POST', 'GET'])
@cross_origin(origin='*')
def handle_service():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            new_service = ServiceModel(
                service_id=data['service_id'], 
                service_type=data['service_type'])

            db.session.add(new_service)
            db.session.commit()

            return {"message": f"Service {new_service.service_id} has been created successfully."}
        else:
            return {"error": "The request payload is not in JSON format"}

    elif request.method == 'GET':
        services = ServiceModel.query.all()
        results = [
            {
                "service_id": services.service_id,
                "service_type": services.service_type
            } for service in services]

        return {"count": len(results), "services": results, "message": "success"}


@app.route('/service/<id>', methods=['GET', 'PUT', 'DELETE'])
@cross_origin(origin='*')
def update_service(id):
    service = ServiceModel.query.get_or_404(payroll)

    if request.method == 'GET':
        response = {
            "service_id": service.service_id,
            "service_type": service.service_type
        }
        return {"message": "success", "service": response}

    elif request.method == 'PUT':
        data = request.get_json()
        service.service_id = data['service_id']
        service.service_type = data['service_type']

        db.session.add(service)
        db.session.commit()
        
        return {"message": f"Service {service.service_id} successfully updated"}

    elif request.method == 'DELETE':
        db.session.delete(service)
        db.session.commit()
        
        return {"message": f"Employee {service.service_id} successfully deleted."}


if __name__ == '__main__':
    app.run(debug=True)
