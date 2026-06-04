"""Parse the assortment scan data the user pasted."""
from collections import Counter, defaultdict
from datetime import datetime

# (yyyymm, ts, visit_id, platform, ip, os, browser_desc, part, action_count)
ROWS = [
    ('202604','2026-04-29 19:19:44','a11c3505808f462fb07b629e49b6a622','mcmaster_com','100.48.144.85','linux','chrome 124.0.0.0 on linux','91375a863',1),
    ('202604','2026-04-29 19:20:24','19b98872843d43729618e123d7994ff6','mobile_website','23.105.149.180','android','chrome mobile 144 pixel 7','91375a745',1),
    ('202604','2026-04-29 19:20:24','cc8209d9f62b41c88af005cc3633e9ee','mobile_website','38.132.124.12','android','chrome mobile 144 pixel 7','91375a767',1),
    ('202604','2026-04-29 19:20:27','4c2ba72314064bbd993d5f0b8a53fe10','mobile_website','87.101.93.234','android','chrome mobile 144 pixel 7','91375a885',1),
    ('202604','2026-04-29 19:20:29','be28ae1950bd406296147fd1b4bf9351','mobile_website','38.206.131.5','android','chrome mobile 144 pixel 7','91375a905',1),
    ('202604','2026-04-29 19:20:30','75a5ac6e835348a8b85eaec2008c8116','mobile_website','23.105.149.198','android','chrome mobile 144 pixel 7','91375a771',1),
    ('202604','2026-04-29 19:20:31','25f378275bdc4cf2aec9d812a4aca34c','mobile_website','87.101.93.234','android','chrome mobile 144 pixel 7','91375a776',1),
    ('202604','2026-04-29 19:20:32','bf57e70eb06a4713ae5491ae9bac5bee','mobile_website','38.206.131.5','android','chrome mobile 144 pixel 7','91375a900',1),
    ('202604','2026-04-29 19:20:35','8cd820821f6e4e0685a7985ef6e1af02','mobile_website','38.205.188.13','android','chrome mobile 144 pixel 7','91375a752',1),
    ('202604','2026-04-29 19:20:37','3c4a7b8e1f4948b2ad5c01700567d2fe','mobile_website','38.202.2.57','android','chrome mobile 144 pixel 7','91375a752',1),
    ('202604','2026-04-29 19:20:40','4b7aa9af787e44f799e2b8527659c562','mobile_website','172.255.126.219','android','chrome mobile 144 pixel 7','91375a905',1),
    ('202604','2026-04-29 19:20:43','6c3ce73ebd0749639f3459401655c2f5','mobile_website','173.208.45.8','android','chrome mobile 144 pixel 7','91375a863',1),
    ('202604','2026-04-29 19:20:45','21d3db2d18aa4eafa00db621049318ea','mobile_website','38.206.131.7','android','chrome mobile 144 pixel 7','91375a745',1),
    ('202604','2026-04-29 19:20:45','b3c62e492c9e4d83aa80e90c6d8554ab','mobile_website','23.105.149.198','android','chrome mobile 144 pixel 7','91375a771',1),
    ('202604','2026-04-29 19:20:46','f5a75c1ed16746a18622776b84bef7d0','mobile_website','108.62.96.8','android','chrome mobile 144 pixel 7','91375a767',1),
    ('202604','2026-04-29 19:20:48','c205029920fd480d9e3c3d6972b42f87','mobile_website','38.206.131.7','android','chrome mobile 144 pixel 7','91375a886',1),
    ('202604','2026-04-29 19:20:49','1477c784002845e18f3812d92df2c9f1','mobile_website','38.206.131.7','android','chrome mobile 144 pixel 7','91375a863',1),
    ('202604','2026-04-29 19:20:49','1b7d3f3d21104f0cbb05f996e8d5d32c','mobile_website','173.208.94.231','android','chrome mobile 144 pixel 7','91375a900',1),
    ('202604','2026-04-29 19:20:53','17d9e4e1dc424ff4b3b5713204eebaf1','mobile_website','64.120.28.52','android','chrome mobile 144 pixel 7','91375a781',1),
    ('202604','2026-04-29 19:20:58','369c4c7ce64a4341b2a9a45d75d5e58d','mobile_website','87.101.93.234','android','chrome mobile 144 pixel 7','91375a776',1),
    ('202604','2026-04-29 19:21:02','2b6a0d1fd7ec41f69d36c5e99299d371','mobile_website','38.205.188.13','android','chrome mobile 144 pixel 7','91375a885',1),
    ('202604','2026-04-29 19:21:02','2be0272b7877486aa9655d89c7025946','mobile_website','23.105.132.5','android','chrome mobile 144 pixel 7','91375a781',1),
    ('202604','2026-04-29 12:24:08','9aa387d7953040e0957cf17d42c53ac6','mobile_website','107.127.28.43','ios','safari 26.3 iphone','91375a745',1),
    ('202604','2026-04-03 07:27:14','1b52c0baeabd402c8d4a92cd0b9e4400','mobile_website','50.233.58.1','ios','safari iphone 18','94723a110',1),
    ('202604','2026-04-02 07:32:00','c8eaaaf425b34548aab4161193d7c983','mobile_website','140.248.30.0','ios','safari 26.2 iphone','90291a144',1),
    ('202604','2026-04-30 07:11:40','89b72421f5a44bc4bfb70c2300bb2479','mobile_website','107.127.28.43','ios','safari 26.3 iphone','91375a745',1),
    ('202604','2026-04-29 10:53:33','30ce07cc2cda4533bf38d1fcf288ee8f','mobile_website','172.59.221.100','ios','safari 26.3 iphone','91375a752',1),
    ('202604','2026-04-29 10:52:39','de41c066e36d43cb8ac1c2bfd27c316a','mobile_website','172.59.221.100','ios','safari 26.3 iphone','91375a886',2),
    ('202605','2026-05-08 10:42:47','cfddc782b7474b668ef409eda631c9ba','mobile_website','50.233.58.1','ios','safari iphone 16','91375a767',1),
    ('202605','2026-05-08 10:43:17','cfddc782b7474b668ef409eda631c9ba','mobile_website','50.233.58.1','ios','safari iphone 16','91375a900',1),
    ('202605','2026-05-08 10:44:08','460c7ef4055d4db2b881ab1773dfceb9','mobile_website','50.233.58.1','ios','safari iphone 17','94723a110',7),
    ('202605','2026-05-08 10:50:51','72b6deccc74942cdacb97705932ed5d7','mobile_website','50.233.58.1','ios','safari iphone 18','94285a350',1),
    ('202605','2026-05-08 10:51:27','811aad4bc92242d8a00f3b60a23200bd','mobile_website','50.233.58.1','ios','safari iphone 17','91375a905',3),
    ('202605','2026-05-08 10:51:38','77f2482b1f6642acb40c5d0e4035905c','mobile_website','50.233.58.1','ios','safari iphone 17','91375a781',1),
    ('202605','2026-05-08 10:52:05','811aad4bc92242d8a00f3b60a23200bd','mobile_website','50.233.58.1','ios','safari iphone 17','91375a745',2),
    ('202605','2026-05-08 10:52:15','811aad4bc92242d8a00f3b60a23200bd','mobile_website','50.233.58.1','ios','safari iphone 17','91375a752',1),
    ('202605','2026-05-08 10:51:06','72b6deccc74942cdacb97705932ed5d7','mobile_website','50.233.58.1','ios','safari iphone 18','94285a325',2),
    ('202605','2026-05-08 10:42:45','167b2fac608b4f798b5718906353f504','android_phone_app','50.233.58.1','android','pixel 9 app','94723a110',9),
    ('202605','2026-05-08 10:31:08','a4227a3ddadb4166afb4590ea7ac8cb4','mobile_website','50.233.58.1','ios','safari iphone 18','94285a520',1),
    ('202605','2026-05-07 13:09:18','7BB998CA28BF430AA80CF0B1D19DE15A','iphone_app','50.233.58.1','ios','iphone18,3 app','94285a515',2),
    ('202605','2026-05-07 17:56:55','93e0e7fca427494a95b05e772e1f9405','android_phone_app','50.233.58.1','android','sm-f966u1 app','94723a110',1),
    ('202605','2026-05-07 17:57:06','93e0e7fca427494a95b05e772e1f9405','android_phone_app','50.233.58.1','android','sm-f966u1 app','91375a905',1),
    ('202605','2026-05-07 15:45:59','06681a9ba3d249d0b5c38e26eb01a624','mobile_website','50.233.58.1','ios','safari iphone 17','94285a360',1),
    ('202605','2026-05-04 09:10:07','b40b19cdd02f4047bde71c46a9da2c5b','android_phone_app','50.233.58.1','android','pixel 7 app','91375a885',1),
    ('202605','2026-05-04 09:09:58','abc28ffccd804f19926ae2cc3146ea11','mobile_website','50.233.58.1','ios','safari 26.3 iphone','91375a886',5),
    ('202605','2026-05-04 09:09:58','8320a17319394755be21499eb237d149','mobile_website','50.233.58.1','ios','safari iphone 18','94285a350',1),
    ('202605','2026-05-04 09:09:58','442a6485585e4a7bbdbf5caeb61b7cd9','mobile_website','161.178.3.235','ios','safari iphone 18','91375a900',1),
    ('202605','2026-05-04 09:10:04','c135e1a80737494395b3a3dec8cef694',None,None,None,None,'91375a781',6),
    ('202605','2026-05-04 09:10:04','db323e2f521144b28d79c62c64d264a2','mobile_website','50.233.58.1','ios','safari iphone 15','91375a900',1),
    ('202605','2026-05-04 09:12:10','c135e1a80737494395b3a3dec8cef694',None,None,None,None,'94723a110',9),
    ('202605','2026-05-04 09:11:19','A56D7C22F725408D8B49300337A3B0E6','iphone_app','50.233.58.1','ios','iphone18,1 app','94723a110',1),
    ('202605','2026-05-04 09:12:22','A56D7C22F725408D8B49300337A3B0E6','iphone_app','50.233.58.1','ios','iphone18,1 app','94285a350',1),
]

ASRT = {
    '94723a110':'A1','94285a315':'A1','94285a325':'A1','94285a350':'A1','94285a360':'A1',
    '94285a455':'A1','94285a460':'A1','94285a510':'A1','94285a515':'A1','94285a520':'A1',
    '94285a610':'A1','94285a615':'A1','94285a620':'A1',
    '94568a110':'A2','90291a074':'A2','90291a077':'A2','90291a103':'A2','90291a106':'A2',
    '90291a143':'A2','90291a144':'A2','90291a189':'A2','90291a190':'A2','90291a533':'A2',
    '90291a537':'A2','90291a825':'A2','90291a826':'A2',
    '94451a110':'A3','91375a745':'A3','91375a752':'A3','91375a767':'A3','91375a771':'A3',
    '91375a776':'A3','91375a781':'A3','91375a826':'A3','91375a863':'A3','91375a885':'A3',
    '91375a886':'A3','91375a900':'A3','91375a905':'A3',
}
MASTERS = {'94723a110','94568a110','94451a110'}

print(f"Total rows: {len(ROWS)}")
internal = [r for r in ROWS if r[4] == '50.233.58.1']
external = [r for r in ROWS if r[4] != '50.233.58.1']
print(f"  Internal (50.233.58.1): {len(internal)}")
print(f"  External:               {len(external)}")

# Pixel 7 / chrome mobile 144 / android 13 burst between 19:19 and 19:21 on 4/29
burst_window = []
for r in ROWS:
    ts = datetime.strptime(r[1], '%Y-%m-%d %H:%M:%S')
    if datetime(2026,4,29,19,19,40) <= ts <= datetime(2026,4,29,19,21,30):
        burst_window.append(r)
print(f"\nApr 29 19:19-19:21 burst rows: {len(burst_window)}")
print(f"  Distinct IPs in burst:        {len({r[4] for r in burst_window})}")
print(f"  All pixel 7 / chrome mobile 144: {all('pixel 7' in (r[6] or '').lower() or 'linux' in (r[6] or '').lower() for r in burst_window)}")
print(f"  Distinct visit_ids in burst:  {len({r[2] for r in burst_window})}")

# After dropping internal + apr29 burst
def is_burst(r):
    ts = datetime.strptime(r[1], '%Y-%m-%d %H:%M:%S')
    return datetime(2026,4,29,19,19,40) <= ts <= datetime(2026,4,29,19,21,30)

real_customer = [r for r in ROWS if r[4] != '50.233.58.1' and not is_burst(r)]
print(f"\nReal customer scans (drop internal + 4/29 burst): {len(real_customer)}")
for r in real_customer:
    print(f"  {r[1]}  {r[7]:>10}  ip={str(r[4]):<18}  acts={r[8]}  visit={r[2][:8]}...")

# By assortment
print("\n=== Real customer scans by assortment ===")
by_asrt = defaultdict(list)
for r in real_customer:
    a = ASRT.get(r[7], '?')
    by_asrt[a].append(r)
for a in sorted(by_asrt):
    rows = by_asrt[a]
    print(f"{a}: {len(rows)} scans, {len({r[7] for r in rows})} distinct parts, {len({r[2] for r in rows})} distinct visits")
