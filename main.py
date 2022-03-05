import time
import musepy.common as muse

note = muse.note("A")
print(note)

v = 0
for i in range(12):
    st = time.time()
    temp = note.flat()
    ed = time.time()
    v += ed - st
    temp = str(temp)
    tempp = tuple([str(x) for x in note.normal()])
    print(f"\tadd semi {i+1}:\t{temp}\t{tempp}")

print(f"Mean time cost of .flat = {v / 12}")
