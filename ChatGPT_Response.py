from ortools.sat.python import cp_model
import pprint
import random

# ----- Fake Dataset -----

# Possible classes with details
all_courses = {
    "Math": {"time_slots": ["Period 1", "Period 2"], "capacity": 30, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
    "English": {"time_slots": ["Period 3", "Period 4"], "capacity": 30, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
    "History": {"time_slots": ["Period 5", "Period 6"], "capacity": 30, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
    "Science": {"time_slots": ["Period 7", "Period 8"], "capacity": 30, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
    "Art": {"time_slots": ["Period 1", "Period 2"], "capacity": 20, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
    "Music": {"time_slots": ["Period 3", "Period 4"], "capacity": 20, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
    "PE": {"time_slots": ["Period 5", "Period 6"], "capacity": 30, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
    "Coding": {"time_slots": ["Period 7", "Period 8"], "capacity": 20, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
    "Drama": {"time_slots": ["Period 1", "Period 2"], "capacity": 20, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
    "Woodshop": {"time_slots": ["Period 3", "Period 4"], "capacity": 20, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
    "Cooking": {"time_slots": ["Period 5", "Period 6"], "capacity": 20, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
    "Robotics": {"time_slots": ["Period 7", "Period 8"], "capacity": 20, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
    "French": {"time_slots": ["Period 1", "Period 2"], "capacity": 20, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
    "Spanish": {"time_slots": ["Period 3", "Period 4"], "capacity": 20, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
    "German": {"time_slots": ["Period 5", "Period 6"], "capacity": 20, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
    "Chinese": {"time_slots": ["Period 7", "Period 8"], "capacity": 20, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
    "Algebra": {"time_slots": ["Period 1", "Period 2"], "capacity": 30, "grade_weight": {"9th": 1, "10th": 1, "11th": 1, "12th": 1}},
}

# Grade levels (for weighting towards specific classes)
grades = ["9th", "10th", "11th", "12th"]

# Time slots
time_slots = ["Period 1", "Period 2", "Period 3", "Period 4", "Period 5", "Period 6", "Period 7", "Period 8"]

def generate_reformatted_student_data(num_students=100):
    students = []
    student_grades = {}
    required_classes = {}
    desired_classes = {}

    for i in range(1, num_students + 1):
        # Randomly assign grade
        grade = random.choice(grades)
        student_grades[i] = grade
        
        # Randomly assign required classes for the student (4-6 required classes)
        required = random.sample(list(all_courses.keys()), random.randint(3, 5))
        required_classes[i] = required
        
        # Randomly assign requested classes (with 2-3 backups each)
        primary = random.sample(list(all_courses.keys()), 5)
        backup = {course: random.sample([c for c in all_courses if c != course], 3) for course in primary}
        desired_classes[i] = {"primary": primary, "backup": backup}
        
        # Combine the data into a student profile
        student = {
            "student_id": i,
            "grade_level": grade,
            "required_classes": required,
            "requested_classes": primary + list(backup.keys()),
        }
        
        students.append(student)
    
    return students, student_grades, required_classes, desired_classes

# Generate the reformatted dataset
students, student_grades, required_classes, desired_classes = generate_reformatted_student_data(10)
pretty_print = pprint.PrettyPrinter(indent=2)
for student in students[:5]:
    pretty_print.pprint(student)

# ----- ORTools CP-SAT Solver -----

# Initialize the model
model = cp_model.CpModel()

# Decision Variables
# x[i][j][t] = 1 if student i is assigned to class j at time t
x = {}
for student in students:
    for course in all_courses:
        for time_slot in all_courses[course]['time_slots']:
            x[(student['student_id'], course, time_slot)] = model.NewBoolVar(f"x_{student['student_id']}_{course}_{time_slot}")

# Constraints

# 1. Required Classes: Each student must be assigned to all required classes
for student in students:
    for course in student['required_classes']:
        # Sum over all possible time slots for class j
        model.Add(sum(x[(student['student_id'], course, t)] for t in all_courses[course]['time_slots']) == 1)

# 2. Class Capacity: No class exceeds its capacity
for course in all_courses:
    for time_slot in all_courses[course]['time_slots']:
        model.Add(
            sum(x[(student['student_id'], course, time_slot)] for student in students) <= all_courses[course]['capacity']
        )

# 3. Time Slot Conflicts: A student cannot be in more than one class at the same time
for student in students:
    for time_slot in time_slots:
        classes_at_t = [course for course in all_courses if time_slot in all_courses[course]['time_slots']]
        if classes_at_t:
            model.Add(sum(x[(student['student_id'], course, time_slot)] for course in classes_at_t) <= 1)

# Objective Function

# Define weights
required_weight = 1000

desired_weight = {}
for student in students:
    student_id = student['student_id']
    desired_weight[student_id] = {}
    desired = desired_classes.get(student_id, {})
    primary = desired.get('primary', [])
    backup = desired.get('backup', [])
    for course in primary:
        grade = student_grades[student_id]
        weight = all_courses[course]['grade_weight'].get(grade, 1)
        desired_weight[student_id][course] = weight
    for course in backup:
        grade = student_grades[student_id]
        weight = all_courses[course]['grade_weight'].get(grade, 1) - 0.5
        desired_weight[student_id][course] = max(weight, 0)

# Build the objective
objective_terms = []

# Add required classes
for student in students:
    student_id = student['student_id']
    for course in required_classes[student_id]:
        for time_slot in all_courses[course]['time_slots']:
            if (student_id, course, time_slot) in x:
                objective_terms.append(x[(student_id, course, time_slot)] * required_weight)

# Add desired classes
for student in students:
    student_id = student['student_id']
    desired = desired_classes.get(student_id, {})
    primary = desired.get('primary', [])
    backup = desired.get('backup', [])
    for course in primary + backup:
        for time_slot in all_courses[course]['time_slots']:
            if (student_id, course, time_slot) in x:
                objective_terms.append(x[(student_id, course, time_slot)] * desired_weight[student_id][course])

# Set the objective to maximize the sum
model.Maximize(sum(objective_terms))

# Solve the model
solver = cp_model.CpSolver()
status = solver.Solve(model)

# Output the results
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    for student in students:
        student_id = student['student_id']
        print(f"\nSchedule for Student {student_id} ({student_grades[student_id]}):")
        for course in all_courses:
            for time_slot in all_courses[course]['time_slots']:
                if solver.Value(x[(student_id, course, time_slot)]) == 1:
                    print(f"  - {course} at Time {time_slot}")
    print(f"Objective Value: {solver.ObjectiveValue()}")
else:
    print("No feasible solution found.")