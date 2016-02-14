cmake_minimum_required(VERSION 3.0.2)
project(yasha)

file(GLOB sources "*.c")
file(GLOB templates "*.jinja")

foreach(tmpl ${templates})
	execute_process(COMMAND yasha ${tmpl} -M OUTPUT_VARIABLE deps)
	string(REGEX REPLACE "^.*: " "" deps ${deps})
	string(REPLACE " " ";" deps ${deps})
	string(REGEX REPLACE "\\.[^.]*$" "" output ${tmpl})
	add_custom_command(
		OUTPUT ${output}
		COMMAND yasha ${tmpl} -o ${output}
		DEPENDS ${deps}
	)
	list(APPEND sources ${output})
endforeach()

add_executable(a.out ${sources})
