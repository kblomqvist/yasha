TEMPLATES = foo.c.jinja foo.h.jinja
SOURCES   = main.c $(filter %.c, $(basename $(TEMPLATES)))
OBJECTS   = $(SOURCES:.c=.o)

program : $(OBJECTS)
	$(CC) $^ -o $@

%.o : %.c | $(filter %.h, $(basename $(TEMPLATES)))
	$(CC) -Wall $< -c -o $@
	$(CC) -MM -MT $@ $< > $*.d

%.c : %.c.jinja
	yasha $< -o $@
	yasha -MM -MT $@ $< > $@.d

%.h : %.h.jinja
	yasha $< -o $@
	yasha -MM -MT $@ $< > $@.d

# Pull in dependency info for existing .o files
-include $(OBJECTS:.o=.d)
-include $(TEMPLATES:.jinja=.d)

clean :
	-rm -f program *.o *.d $(basename $(TEMPLATES))

.phony : clean

# Disable Make built-in rules
.suffixes :

# Prevent Make to consider rendered templates as intermediate file
.secondary : $(basename $(TEMPLATES))
