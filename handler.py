from mangum import Mangum

import wa.app

app = wa.app.create()
handler = Mangum(app)
