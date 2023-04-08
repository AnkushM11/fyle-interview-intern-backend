"""
API's for teacher assignments resource.
"""

# importing the necessary packages
from flask import Blueprint
from core import db
from core.apis import decorators
from core.apis.responses import APIResponse
from core.models.assignments import Assignment

# Importing the AssignmentSchema
from .schema import AssignmentSchema, AssignmentGradingSchema

# Creating Blueprint for the teacher_assignments_resources
teacher_assignments_resources = Blueprint('teacher_assignments_resources', __name__)


# GET /teacher/assignments route
@teacher_assignments_resources.route('/assignments', methods=['GET'], strict_slashes=False)
@decorators.auth_principal
def list_assignments(p):
    """Returns list of all assignments submitted to this teacher"""

    # Calling the get_assignments_submitted_to_teacher method to get
    # all the assignments submitted to the teacher using teacher_id
    teacher_assignments = Assignment.get_assignments_submitted_to_teacher(p)


    # Calling the dump method to get json format of assignment
    teacher_assignments_dump = AssignmentSchema().dump(teacher_assignments, many=True)

    # returning all assignments submitted to this teacher
    return APIResponse.respond(data=teacher_assignments_dump)


# POST /student/assignments/submit route
@teacher_assignments_resources.route('/assignments/grade', methods=['POST'], strict_slashes=False)
@decorators.accept_payload
@decorators.auth_principal
def grade_assignment(p, incoming_payload):
    """Grade an assignment by the teacher."""

    # Getting the payload from the request containing id (assignment id) and teacher_id(id of teacher)
    grade_assignment_payload = AssignmentGradingSchema().load(incoming_payload)

    # Calling the grading method to update the grade of a submitted assignment
    graded_assignment = Assignment.grading(
        _id=grade_assignment_payload.id,
        grade=grade_assignment_payload.grade,
        principal=p
    )

    # commiting the changes to database
    db.session.commit()

    # Calling the dump method to get json format of assignment
    graded_assignment_dump = AssignmentSchema().dump(graded_assignment)

    # returning assignment graded by the teacher
    return APIResponse.respond(data=graded_assignment_dump)
