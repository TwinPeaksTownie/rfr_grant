import json, box_client as bc

# 1. folder structure
root = bc.create_folder("Reach Forward Robotics", "0")
raw = bc.create_folder("01_raw", root)
dossiers = bc.create_folder("02_dossiers", root)
drafts = bc.create_folder("03_drafts", root)
folders = {"root": root, "raw": raw, "dossiers": dossiers, "drafts": drafts}
json.dump(folders, open("box_folders.json", "w"))
print("folders:", folders)

# 2. profile doc (grounds every outreach draft + qualification)
PROFILE = """REACH FORWARD ROBOTICS - ORGANIZATION PROFILE

WHAT WE ARE
Reach Forward Robotics is an open-source robotics league for students, launching as
a one-year pilot across East King County, Washington (King County District 3:
Redmond, Sammamish, Issaquah, Woodinville, Bothell, North Bend, Snoqualmie). We are
a nonprofit in formation. Our model: put open-source humanoid robots (Hugging Face
Reachy Mini) directly into student hands and run a regional competition series that
generates real open-source contributions.

LEGAL STATUS
Nonprofit in formation. We apply as Reach Forward Robotics. Grants that require an
already-active 501(c)(3) should be flagged as pending incorporation; grants open to
nonprofits-in-formation, fiscally-sponsored projects, educators, or schools are
immediately actionable.

MISSION AND MODEL
Inspired by the 1982 Apple IIe school donation that seeded a generation of builders,
we want open-source robotics in student hands now. Deployment goal: 250 Reachy Mini
robots, 9 schools, 4 competitions over a one-year pilot. Competition series includes
an off-road Reachy rally, a LeRobot SO-101 creative challenge, and a Gradio
King-of-the-Hill event.

WHO WE SERVE
High school students and robotics clubs in East King County, one of the highest
concentrations of students with AI-engineer parents in the U.S. Lake Washington
School District is the 2nd fastest-growing district in Washington State.

WHAT WE ARE SEEKING
1. Grant funding for STEM/technology education, youth education, robotics, AI
   literacy, makerspaces, and workforce development.
2. In-kind hardware and compute donations: robots (Reachy Mini), edge-AI hardware
   (NVIDIA Jetson, Seeed Studio kits), and cloud/compute credits for student model
   training.

TRACTION
- Live demo at Mt. Si High School Si Borgs Robotics Club (students spent ~3 hours
  asking about DOF, kinematics, FFT).
- Demo at North Bend City Hall for the Mayor, Head of IT, Finance, and City Manager.
- Doors Open King County launch grant active. LeRobot Hub-native curriculum discussed
  with the North Bend mayor.

PROJECT LEAD
Carson Maestas, Snoqualmie WA. Hugging Face Reachy Mini beta tester and developer.
Procurement background (Boeing, AT&T, T-Mobile). Deep roots in East King County.
Contact: carson@twinpeakstownie.com

TONE FOR OUTREACH
Concrete and specific, never generic. Lead with the student impact and the
open-source angle. Reference the funder's actual program by name. No filler.
"""
pid = bc.upload_text("Reach_Forward_Profile.txt", PROFILE, root)
json.dump({"profile_file_id": pid}, open("box_profile.json", "w"))
print("profile uploaded, file id:", pid)
