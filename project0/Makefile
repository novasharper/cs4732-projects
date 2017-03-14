# compiler
CC = g++

# linker
LD = g++

# compiler flags
CFLAGS = -Wno-deprecated  -I.

# linker flags
LDFLAGS = -lglut -lGL -lGLU -L/usr/X11R6/lib -lX11 -lXmu -lXi -lm

# used to clean
RM = /bin/rm -f

# generated object files
OBJS = cs4732_proj0.o

#program file name
PROG = proj0

# to compile everything
all: $(PROG)

# linking the program
$(PROG): $(OBJS)
	$(LD) $(OBJS) $(LDFLAGS) -o $(PROG)

cs4732_proj0.o: cs4732_proj0.cpp
	$(CC) $(CFLAGS) -c cs4732_proj0.cpp

# cleanup
clean:
	$(RM) $(PROG) $(OBJS)
