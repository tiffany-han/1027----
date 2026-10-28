import pandas as pd, sys
D=sys.argv[1] if len(sys.argv)>1 else 'islemart_data'
r=lambda n: pd.read_csv(f'{D}/{n}', encoding='utf-8-sig')
o=r('islemart_orders_dataset.csv'); it=r('islemart_order_items_dataset.csv'); pay=r('islemart_order_payments_dataset.csv')
rv=r('islemart_order_reviews_dataset.csv'); c=r('islemart_customers_dataset.csv'); p=r('islemart_products_dataset.csv'); s=r('islemart_sellers_dataset.csv'); tr=r('product_category_name_translation.csv')
# 價格異常：單價 >= 同類別中位數 20 倍（多打兩個 0）
_cat=it.product_id.map(p.set_index('product_id').product_category_name).fillna('（未分類）')
it['outlier']=it.price>=20*it.groupby(_cat).price.transform('median')
for col in ['order_purchase_timestamp','order_approved_at','order_delivered_carrier_date','order_delivered_customer_date','order_estimated_delivery_date']:
    o[col]=pd.to_datetime(o[col])
print('status', o.order_status.value_counts().to_dict())
dl=o[o.order_status=='delivered'].copy()
# GMV (delivered, items price incl. outliers) and cleaned
itd=it[it.order_id.isin(dl.order_id)]
print('GMV delivered price sum', itd.price.sum(), 'freight', itd.freight_value.sum())
print('price outliers (20x category median)', it.outlier.sum())
print('GMV excl outliers', itd[~itd.outlier].price.sum())
dl['ym']=dl.order_purchase_timestamp.dt.to_period('M')
m=itd.merge(dl[['order_id','ym']]).query('~outlier').groupby('ym').price.sum()
print('monthly GMV\n', m.to_string())
print('payments total', pay.payment_value.sum(), 'items total all orders', (it.price+it.freight_value).sum())
po=pay.groupby('order_id').payment_value.sum(); io=(it.assign(t=it.price+it.freight_value)).groupby('order_id').t.sum()
diff=(po-io).abs(); print('orders pay!=items (>1)', (diff>1).sum(), ' multi-payment orders', (pay.groupby('order_id').size()>1).sum())
v=dl.dropna(subset=['order_delivered_customer_date'])
v=v[v.order_delivered_customer_date>=v.order_delivered_carrier_date]
v['days']=(v.order_delivered_customer_date-v.order_purchase_timestamp).dt.total_seconds()/86400
v['late']=v.order_delivered_customer_date.dt.normalize()>v.order_estimated_delivery_date
print('avg delivery days', round(v.days.mean(),2), 'late rate', round(v.late.mean()*100,2))
print('anomaly delivered<carrier', (dl.order_delivered_customer_date<dl.order_delivered_carrier_date).sum(), ' delivered missing date', dl.order_delivered_customer_date.isna().sum(), ' canceled with delivered date', o[(o.order_status=='canceled')&o.order_delivered_customer_date.notna()].shape[0])
rvd=rv.drop_duplicates().drop_duplicates('order_id')
x=v.merge(rvd[['order_id','review_score']])
print('avg score late vs on-time', x.groupby('late').review_score.mean().round(2).to_dict())
x['ld']=(x.order_delivered_customer_date.dt.normalize()-x.order_estimated_delivery_date).dt.days
x['bucket']=pd.cut(x.ld,[-99,0,4,99],labels=['on time','1-4 late','>4 late'])
print(x.groupby('bucket',observed=True).review_score.agg(['mean','count']).round(2))
cv=v.merge(c[['customer_id','customer_county']]); cv['county']=cv.customer_county.str.replace('臺','台')
print('late rate by county\n', cv.groupby('county').late.mean().mul(100).round(1).sort_values(ascending=False).head(8).to_string())
print('avg days by county top\n', cv.groupby('county')['days'].mean().round(1).sort_values(ascending=False).head(6).to_string())
print('county 臺 variants', c.customer_county.str.startswith('臺').sum())
print('reviews: exact dup rows', rv.duplicated().sum(), ' orders with >1 review', (rv.drop_duplicates().groupby('order_id').size()>1).sum(), ' empty msg %', round(rv.review_comment_message.isna().mean()*100,1))
print('score dist', rvd.review_score.value_counts(normalize=True).sort_index().round(3).to_dict())
cc=c.groupby('customer_unique_id').size(); print('unique customers', len(cc), ' repeat buyers', (cc>1).sum(), ' repeat %', round((cc>1).mean()*100,2))
print('products missing category', p.product_category_name.isna().sum(), ' categories missing translation', sorted(set(p.product_category_name.dropna())-set(tr.product_category_name)))
cat=itd.merge(p[['product_id','product_category_name']]).query('~outlier').groupby('product_category_name').price.sum().sort_values(ascending=False)
print('category GMV top\n', cat.head(6).to_string())
ss=v.merge(it[['order_id','seller_id']].drop_duplicates('order_id')).groupby('seller_id').agg(n=('late','size'),late=('late','mean'))
print('sellers late>30% with >=50 orders', ((ss.late>0.3)&(ss.n>=50)).sum(), ' overall seller median late', round(ss.late.median()*100,1))
print('pay types', pay.payment_type.value_counts().to_dict())
dd=o.order_purchase_timestamp.dt.date.value_counts(); print('top days', dd.head(5).to_dict())
