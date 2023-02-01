#!/bin/bash

# Clear framebuffer suppressing dd's "No space left on device" error 
/bin/dd if=/dev/zero of=/dev/fb0 &> /dev/null
exit 0
