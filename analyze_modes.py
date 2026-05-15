"""Analyze order entry mode by contact_id."""
import pandas as pd
import numpy as np

FILE = '/root/.claude/uploads/528ddbad-9222-45b5-bf2e-c5fcee20e8b8/cf2ff394-Order_Modes_By_Contact_IDs.csv'

df = pd.read_csv(FILE)
df.columns = df.columns.str.strip().str.lstrip('﻿')
print(f"Rows: {len(df):,}")
print(f"Columns: {df.columns.tolist()}\n")

mode_cols = ['web','email','phone','ecmrc','mobile','edi','fax','other']

# ============================================================================
print("="*70)
print("1. DATASET TOTALS")
print("="*70)
print(f"Unique contacts:     {len(df):,}")
print(f"Total orders:        {df['total_orders'].sum():,}")
print(f"Sum of mode columns: {df[mode_cols].sum().sum():,}  (sanity check)")
print()

# ============================================================================
print("="*70)
print("2. ORDER VOLUME BY CHANNEL")
print("="*70)
totals = df[mode_cols].sum().sort_values(ascending=False)
grand = totals.sum()
for ch, n in totals.items():
    print(f"  {ch:8s} {n:>12,}  ({n/grand*100:5.1f}%)")
print()

# ============================================================================
print("="*70)
print("3. CONTACTS USING EACH CHANNEL (≥1 order in that channel)")
print("="*70)
total_contacts = len(df)
for ch in mode_cols:
    n = (df[ch] > 0).sum()
    print(f"  {ch:8s} {n:>10,} contacts  ({n/total_contacts*100:5.1f}% of contacts)")
print()

# ============================================================================
print("="*70)
print("4. CHANNEL MIX — what channel dominates per contact?")
print("="*70)
df['primary_channel'] = df[mode_cols].idxmax(axis=1)
df['primary_pct']     = df[mode_cols].max(axis=1) / df['total_orders'] * 100

print("Primary channel = the mode with the most orders for that contact:")
prim = df['primary_channel'].value_counts()
for ch, n in prim.items():
    orders = df.loc[df['primary_channel']==ch, 'total_orders'].sum()
    print(f"  {ch:8s}  {n:>10,} contacts  ({n/total_contacts*100:5.1f}%)   their total orders: {orders:>12,}")
print()

# ============================================================================
print("="*70)
print("5. MULTI-CHANNEL CONTACTS (mode-switching)")
print("="*70)
df['channels_used'] = (df[mode_cols] > 0).sum(axis=1)
mc = df['channels_used'].value_counts().sort_index()
for n, count in mc.items():
    print(f"  {n} channel(s): {count:>10,} contacts  ({count/total_contacts*100:5.1f}%)")

print()
print("Among multi-channel contacts (uses ≥2 channels):")
multi = df[df['channels_used'] >= 2]
print(f"  Contacts: {len(multi):,} ({len(multi)/total_contacts*100:.1f}%)")
print(f"  Orders:   {multi['total_orders'].sum():,} ({multi['total_orders'].sum()/df['total_orders'].sum()*100:.1f}% of all orders)")
print()

# ============================================================================
print("="*70)
print("6. WEB-FIRST vs OTHER-FIRST CONTACTS")
print("="*70)
df['web_pct']    = df['web']    / df['total_orders'] * 100
df['nonweb_pct'] = 100 - df['web_pct']

bins = [-0.1, 0, 20, 50, 80, 99.9, 100.1]
labels = ['0% web', '1-20% web', '21-50% web', '51-80% web', '81-99% web', '100% web']
df['web_bucket'] = pd.cut(df['web_pct'], bins=bins, labels=labels)
wb = df.groupby('web_bucket', observed=True).agg(
    contacts=('contact_id','count'),
    total_orders=('total_orders','sum')
).reset_index()
wb['contacts_pct'] = wb['contacts']/total_contacts*100
wb['orders_pct']   = wb['total_orders']/df['total_orders'].sum()*100
print(wb.to_string(index=False, formatters={
    'contacts': '{:,}'.format,
    'total_orders': '{:,}'.format,
    'contacts_pct': '{:.1f}%'.format,
    'orders_pct': '{:.1f}%'.format,
}))
print()

# ============================================================================
print("="*70)
print("7. MODE SWITCHING — sprint question: 80% web / 20% other contacts?")
print("="*70)
heavyweb = df[(df['web_pct'] >= 70) & (df['web_pct'] < 100)]
print(f"Contacts placing 70-99% of orders on web (the 'mostly web' segment):")
print(f"  {len(heavyweb):,} contacts ({len(heavyweb)/total_contacts*100:.1f}%)")
print(f"  Total orders: {heavyweb['total_orders'].sum():,}")
print(f"  Of which: web    {heavyweb['web'].sum():,}    ({heavyweb['web'].sum()/heavyweb['total_orders'].sum()*100:.1f}%)")
nonweb_total = heavyweb['total_orders'].sum() - heavyweb['web'].sum()
print(f"           non-web {nonweb_total:,}    ({nonweb_total/heavyweb['total_orders'].sum()*100:.1f}%)")
print()
print("Non-web channel breakdown for the 'mostly web' segment:")
for ch in mode_cols:
    if ch == 'web': continue
    n = heavyweb[ch].sum()
    if n > 0:
        print(f"  {ch:8s} {n:>10,}  ({n/nonweb_total*100:5.1f}% of their non-web orders)")
print()

# ============================================================================
print("="*70)
print("8. CMFs PER CONTACT")
print("="*70)
print(f"Median distinct CMFs per contact: {df['distinct_cmfs'].median():.0f}")
print(f"Mean:                              {df['distinct_cmfs'].mean():.2f}")
print(f"Max:                               {df['distinct_cmfs'].max()}")
print()
cmf_buckets = pd.cut(df['distinct_cmfs'], bins=[0,1,2,3,5,10,1000], labels=['1','2','3','4-5','6-10','11+'])
cmfb = cmf_buckets.value_counts().sort_index()
for b, n in cmfb.items():
    print(f"  {b:5s} CMFs: {n:>10,} contacts ({n/total_contacts*100:5.1f}%)")
print()

# ============================================================================
print("="*70)
print("9. TOP 20 CONTACTS BY ORDER VOLUME")
print("="*70)
top = df.nlargest(20, 'total_orders')[['contact_id','total_orders','web','email','phone','ecmrc','mobile','distinct_cmfs','primary_channel']]
print(top.to_string(index=False))
