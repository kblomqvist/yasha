TEMPLATES = foo.c.jinja foo.h.jinja
SOURCES   = main.c $(filter %.c, $(basename $(TEMPLATES)))
OBJECTS   = $(SOURCES:.c=.o)

DEPENDENCIES = $(OBJECTS:.o=.d) $(TEMPLATES:.jinja=.d)

program : $(OBJECTS)
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
	-rm -f program
	-rm -f $(OBJECTS)
	-rm -f $(DEPENDENCIES)
	-rm -f $(basename $(TEMPLATES))

.phony : clean
