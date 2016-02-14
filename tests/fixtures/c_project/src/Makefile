# User variables
SOURCES    = $(wildcard *.c)
TEMPLATES  = $(wildcard *.jinja)
EXECUTABLE = a.out

# Add rendered .c templates to sources list
SOURCES += $(filter %.c, $(basename $(TEMPLATES)))

# Resolve build dir from executable
BUILDDIR = $(dir $(EXECUTABLE))

# Resolve object files
OBJECTS = $(addprefix $(BUILDDIR), $(SOURCES:.c=.o))

# Resolve .d files which list what files the object
# and template files depend on
OBJECTS_D   = $(OBJECTS:.o=.d)
TEMPLATES_D = $(addsuffix .d,$(basename $(TEMPLATES)))

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
	-rm -f $(OBJECTS_D)
else
	-rm -rf $(BUILDDIR)
endif
	-rm -f $(TEMPLATES_D)
	-rm -f $(basename $(TEMPLATES))

.phony : clean
