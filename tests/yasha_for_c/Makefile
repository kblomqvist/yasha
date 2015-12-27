# User variables
SOURCES    = $(wildcard src/*.c)
TEMPLATES  = $(wildcard src/*.jinja)
EXECUTABLE = build/a.out

# Add rendered .c templates to sources list
SOURCES += $(filter %.c, $(basename $(TEMPLATES)))

# Resolve build dir from executable
BUILDDIR = $(dir $(EXECUTABLE))

# Resolve object files along with the .d files which lists what files
# the object and template file depends on
OBJECTS     = $(addprefix $(BUILDDIR), $(SOURCES:.c=.o))
OBJECTS_D   = $(OBJECTS:.o=.d)
TEMPLATES_D = $(TEMPLATES:.jinja=.d)

$(EXECUTABLE) : $(OBJECTS)
	$(CC) $^ -o $@

$(BUILDDIR)%.o : %.c | $(filter %.h, $(basename $(TEMPLATES)))
	@mkdir -p $(dir $@)
	$(CC) -MMD -MP $< -c -o $@

%.c : %.c.jinja
	yasha -MD $< -o $@

%.h : %.h.jinja
	yasha -MD $< -o $@

# Make sure that the following built-in implicit rule is cancelled
%.o : %.c

# Pull in dependency info for existing .o and template files
-include $(OBJECTS_D) $(TEMPLATES_D)

# Prevent Make to consider rendered templates as intermediate file
.secondary : $(basename $(TEMPLATES))

clean :
ifeq ($(BUILDDIR),./)
	-rm -f $(EXECUTABLE)
	-rm -f $(OBJECTS)
else
	-rm -rf $(BUILDDIR)
endif
	-rm -f $(TEMPLATES_D)
	-rm -f $(basename $(TEMPLATES))

.phony : clean