{
 "module_name": "migration_portal",
 "export_fixtures": [
  {
   "doctype": "Migration Service"
  },
  {
   "doctype": "Workflow",
   "filters": {
    "name": ["in", ["Inquiry Process", "Client Process"]]
   }
  }
 ],
 "app_include_js": "/assets/migration_portal/js/migration_portal.js",
 "app_include_css": "/assets/migration_portal/css/migration_portal.css",
 "doc_events": {
  "Inquiry": {
   "on_update": "migration_portal.migration_portal.doctype.inquiry.inquiry.Inquiry.on_update",
   "on_submit": "migration_portal.migration_portal.doctype.inquiry.inquiry.Inquiry.on_submit",
   "on_cancel": "migration_portal.migration_portal.doctype.inquiry.inquiry.Inquiry.on_cancel"
  },
  "Client": {
   "on_update": "migration_portal.migration_portal.doctype.client.client.Client.on_update",
   "on_submit": "migration_portal.migration_portal.doctype.client.client.Client.on_submit",
   "on_cancel": "migration_portal.migration_portal.doctype.client.client.Client.on_cancel"
  },
  "Migration Payment": {
   "on_submit": "migration_portal.migration_portal.doctype.migration_payment.migration_payment.MigrationPayment.on_submit",
   "on_cancel": "migration_portal.migration_portal.doctype.migration_payment.migration_payment.MigrationPayment.on_cancel"
  }
 }
} 