cmake_minimum_required(VERSION 2.8.7)
project(yasha)

file(GLOB sources "src/*.c")
file(GLOB templates "src/*.jinja")

foreach(tmpl ${templates})
    string(REGEX REPLACE "\\.[^.]*$" "" output ${tmpl})
    execute_process(
        COMMAND yasha ${tmpl} -M
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        OUTPUT_VARIABLE deps
    )
    string(REGEX REPLACE "^.*: " "" deps ${deps})
    string(REPLACE " " ";" deps ${deps})
    add_custom_command(
        OUTPUT ${output}
        COMMAND yasha ${tmpl} -o ${output}
        DEPENDS ${deps}
    )
    list(APPEND sources ${output})
endforeach()

add_executable(a.out ${sources})
