db.define_table('scripts_table',
                Field('code', type='text',
                      label='Script code'),
                Field('last_usage_time', type='datetime',
                      label='Last usage time',
                      default=request.now),
                )


