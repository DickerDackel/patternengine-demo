# patternengine-demo

Demo showcasing many patterns from the patternengine project

[You can watch it here](https://youtu.be/HtlNjl8-Zd0?si=HTU4GRDHWqJFArzt)

This code here is provided to study some of my weird packages and classes, e.g.

    * pgcooldown with Cooldown, LerpThing and CronD
    * tinyecs
    * patternengine
    * Lots of functool.partial to fake "lazy evaluation"

# Installation

You are using virtual envs, aren't you?  AREN'T YOU?

I pull in a lot of shit that might have a yet unstable API, so don't ruin your
main python install.

```
python -m venv patternengine-demo
cd patternengine-demo

Scripts\activate.bat
# or on linux
# source ./bin/activate

pip install git+https://github.com/dickerdackel/patternengine-demo

patternengine-demo
```
