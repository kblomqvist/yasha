cmake_minimum_required(VERSION 3.0.2)
project(yasha)

file(GLOB SOURCES "src/*.c")
file(GLOB TEMPLATES "src/*.jinja")

foreach(input ${TEMPLATES})
	string(REGEX REPLACE "\\.[^.]*$" "" output ${input})
	list(APPEND SOURCES ${output})
	add_custom_command(
		OUTPUT ${output}
		COMMAND yasha ${input} -o ${output}
	)
endforeach()

add_executable(a.out ${SOURCES})