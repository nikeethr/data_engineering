cf_dist_id=E1YSWETVNIIGUQ

aws cloudfront create-invalidation --distribution-id $cf_dist_id --paths "/about.shtml"
