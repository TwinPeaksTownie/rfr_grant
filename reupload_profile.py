import json, box_client as bc
folders=json.load(open("box_folders.json"))
PROFILE = """REACH FORWARD ROBOTICS - ORGANIZATION PROFILE

WHAT WE ARE
Reach Forward Robotics is an open-source robotics league for students, launching as a one-year
pilot across East King County, Washington (King County District 3: Redmond, Sammamish, Issaquah,
Woodinville, Bothell, North Bend, Snoqualmie). We put open-source humanoid robots (Hugging Face
Reachy Mini) directly into student hands and run a regional competition series that generates real
open-source contributions.

LEGAL STATUS (internal note for routing, not for outreach copy)
Reach Forward Robotics is the applying organization, a Washington nonprofit. 501(c)(3) registration
is being finalized; where a funder requires active 501(c)(3) status we apply either as the
registered nonprofit or under an established fiscal sponsor. In outreach, present Reach Forward
Robotics simply as the applicant organization. Do not state we are "in formation," do not apologize
for status, do not invent an EIN or registration date.

MISSION AND MODEL
Inspired by the 1982 Apple IIe school donation that seeded a generation of builders, we want
open-source robotics in student hands now. Deployment goal: 250 Reachy Mini robots, 9 schools,
4 competitions over a one-year pilot. Competition series includes an off-road Reachy rally, a
LeRobot SO-101 creative challenge, and a Gradio King-of-the-Hill event.

WHO WE SERVE
High school students and robotics clubs in East King County, one of the highest concentrations of
students with AI-engineer parents in the U.S. Lake Washington School District is the 2nd
fastest-growing district in Washington State.

WHAT WE ARE SEEKING
1. Grant funding for STEM/technology education, youth education, robotics, AI literacy,
   makerspaces, and workforce development.
2. In-kind hardware and compute donations: robots (Reachy Mini), edge-AI hardware (NVIDIA Jetson,
   Seeed Studio kits), and cloud/compute credits for student model training.

TRACTION (only cite what is here)
- Live demo at Mt. Si High School Si Borgs Robotics Club; students spent ~3 hours asking about
  degrees of freedom, kinematics, and FFT.
- Demo at North Bend City Hall for the Mayor, Head of IT, Finance, and City Manager.
- Doors Open King County launch grant active.

PROJECT LEAD
Carson Maestas, Snoqualmie WA. Hugging Face Reachy Mini beta tester and developer. Procurement
background (Boeing, AT&T, T-Mobile). Contact: carson@twinpeakstownie.com

TONE FOR OUTREACH
Concrete and specific, never generic. Lead with student impact and the open-source angle.
Reference the funder's actual program by name. No filler. Invent nothing.
"""
open("Reach_Forward_Profile.txt","w").write(PROFILE)
pid=bc.upload_text("Reach_Forward_Profile.txt", PROFILE, folders["root"])
json.dump({"profile_file_id":pid}, open("box_profile.json","w"))
print("profile re-uploaded, id:", pid)
