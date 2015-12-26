SOURCES    = main.c
TEMPLATES  = foo.c.jinja foo.h.jinja
EXECUTABLE = a.out

# Add rendered .c templates to sources list
SOURCES += $(filter %.c, $(basename $(TEMPLATES)))

# Resolve object files along with the .d files which lists what files
# the object and template file depends on
OBJECTS      = $(SOURCES:.c=.o)
DEPENDENCIES = $(OBJECTS:.o=.d) $(TEMPLATES:.jinja=.d)

$(EXECUTABLE) : $(OBJECTS)
	$(CC) $^ -o $@

%.o : %.c | $(filter %.h, $(basename $(TEMPLATES)))
	$(CC) -MMD -MP $< -c -o $@

%.c : %.c.jinja
	yasha -MD $< -o $@

%.h : %.h.jinja
	yasha -MD $< -o $@

# Make sure that the following built-in implicit rule is cancelled
%.o : %.c

# Pull in dependency info for existing .o and template files
-include $(DEPENDENCIES)

# Prevent Make to consider rendered templates as intermediate file
.secondary : $(basename $(TEMPLATES))

clean :
	-rm -f $(EXECUTABLE)
	-rm -f $(OBJECTS)
	-rm -f $(DEPENDENCIES)
	-rm -f $(basename $(TEMPLATES))

.phony : clean