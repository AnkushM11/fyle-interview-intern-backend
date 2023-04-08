import enum
from core import db
from core.apis.decorators import Principal
from core.libs import helpers, assertions
from core.models.teachers import Teacher
from core.models.students import Student
from sqlalchemy.types import Enum as BaseEnum



class GradeEnum(str, enum.Enum):
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'


class AssignmentStateEnum(str, enum.Enum):
    DRAFT = 'DRAFT'
    SUBMITTED = 'SUBMITTED'
    GRADED = 'GRADED'


class Assignment(db.Model):
    __tablename__ = 'assignments'
    id = db.Column(db.Integer, db.Sequence('assignments_id_seq'), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey(Student.id), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey(Teacher.id), nullable=True)
    content = db.Column(db.Text)
    grade = db.Column(BaseEnum(GradeEnum))
    state = db.Column(BaseEnum(AssignmentStateEnum), default=AssignmentStateEnum.DRAFT, nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), default=helpers.get_utc_now, nullable=False)
    updated_at = db.Column(db.TIMESTAMP(timezone=True), default=helpers.get_utc_now, nullable=False, onupdate=helpers.get_utc_now)

    def __repr__(self):
        return '<Assignment %r>' % self.id

    @classmethod
    def filter(cls, *criterion):
        db_query = db.session.query(cls)
        return db_query.filter(*criterion)

    @classmethod
    def get_by_id(cls, _id):
        return cls.filter(cls.id == _id).first()

    @classmethod
    def upsert(cls, assignment_new: 'Assignment'):
        if assignment_new.id is not None:
            assignment = Assignment.get_by_id(assignment_new.id)
            assertions.assert_found(assignment, 'No assignment with this id was found')
            assertions.assert_valid(assignment.state == AssignmentStateEnum.DRAFT,
                                    'only assignment in draft state can be edited')

            assignment.content = assignment_new.content
        else:
            assignment = assignment_new
            db.session.add(assignment_new)

        db.session.flush()
        return assignment

    @classmethod
    def submit(cls, _id, teacher_id, principal: Principal):
        assignment = Assignment.get_by_id(_id)

        #Check if student exists
        student = Student.get_student(principal.user_id)
        assertions.assert_found(student, 'No student with this user id.')

        assertions.assert_found(assignment, 'No assignment with this id was found')
        assertions.assert_valid(assignment.student_id == principal.student_id, 'This assignment belongs to some other student')
        assertions.assert_valid(assignment.content is not None, 'assignment with empty content cannot be submitted')

        # Only draft assignment can be submitted to teacher
        # Checking if the state of assignment is in draft state else raise an error
        assertions.assert_valid(assignment.state == AssignmentStateEnum.DRAFT, 'only a draft assignment can be submitted')

        assignment.teacher_id = teacher_id
        assignment.state = AssignmentStateEnum.SUBMITTED
        db.session.flush()

        return assignment


    @classmethod
    def get_assignments_by_student(cls, principal: Principal):
        # Checking if the student exists
        student = Student.get_student(principal.user_id)
        assertions.assert_found(student, 'No student with this user id.')
        return cls.filter(cls.student_id == principal.student_id).all()



    # A classmethod to return all the assignments submitted to the teacher
    # using the filter method to get all assignments corresponding to given teacher_id
    @classmethod
    def get_assignments_submitted_to_teacher(cls, principal: Principal):
        # Checking if the teacher exists
        teacher = Teacher.get_teacher(principal.user_id)
        assertions.assert_found(teacher, 'No teacher with this user id.')
        return cls.filter(cls.teacher_id == principal.teacher_id).all()



    @classmethod
    def grading(cls, _id, grade, principal: Principal):

        # getting the assignent using id attribute
        assignment = Assignment.get_by_id(_id)

        # Check if teacher exists
        teacher = Teacher.get_teacher(principal.user_id)
        assertions.assert_found(teacher, 'No teacher with this user id.')

        # Checking if the assignment is present in the database.
        # Assignment should be valid
        assertions.assert_found(assignment, 'No assignment with this id was found')

        # Checking if the assignment was graded only by the teacher to whom it was submitted
        # teacher_1 cannot grade assignments which were submitted to teacher_2
        assertions.assert_valid(assignment.teacher_id == principal.teacher_id, 'This assignment was submitted to some other teacher.')

        # Checking if the assignment state was SUBMITTED
        # Only assignments in SUBMITTED state can be graded
        assertions.assert_valid(assignment.state == AssignmentStateEnum.SUBMITTED, 'only a submitted assignment can be graded')

        # Assigning the grade to the assignment
        assignment.grade = grade

        # Changing the assignment state to GRADED
        assignment.state = AssignmentStateEnum.GRADED

        db.session.flush()

        return assignment


