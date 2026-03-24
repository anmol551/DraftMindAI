from generators.abstract_gen import generate_abstract
from generators.introduction_gen import generate_introduction
from generators.methodology_gen import generate_methodology
from generators.implementation_gen import generate_implementation
from generators.result_gen import generate_result_conclusion
from keywords import generate_keywords
from get_citation import get_ref_citation


# generate_keywords()

# get_ref_citation()
# print("Done")

generate_abstract()
print("Abstract Generated!")

generate_introduction()
print("Introduction Generated!")

generate_methodology()
print("Methodology Generated!")

generate_implementation()
print("Implementation Generated!")

generate_result_conclusion()
print("Result Generated!")