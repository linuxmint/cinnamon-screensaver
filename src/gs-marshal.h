
#ifndef __gs_marshal_MARSHAL_H__
#define __gs_marshal_MARSHAL_H__

#include	<glib-object.h>

G_BEGIN_DECLS

/* BOOLEAN:VOID (gs-marshal.list:1) */
extern void gs_marshal_BOOLEAN__VOID (GClosure     *closure,
                                      GValue       *return_value,
                                      guint         n_param_values,
                                      const GValue *param_values,
                                      gpointer      invocation_hint,
                                      gpointer      marshal_data);

/* BOOLEAN:INT (gs-marshal.list:2) */
extern void gs_marshal_BOOLEAN__INT (GClosure     *closure,
                                     GValue       *return_value,
                                     guint         n_param_values,
                                     const GValue *param_values,
                                     gpointer      invocation_hint,
                                     gpointer      marshal_data);

/* BOOLEAN:BOOLEAN (gs-marshal.list:3) */
extern void gs_marshal_BOOLEAN__BOOLEAN (GClosure     *closure,
                                         GValue       *return_value,
                                         guint         n_param_values,
                                         const GValue *param_values,
                                         gpointer      invocation_hint,
                                         gpointer      marshal_data);

/* VOID:STRING,STRING,STRING (gs-marshal.list:4) */
extern void gs_marshal_VOID__STRING_STRING_STRING (GClosure     *closure,
                                                   GValue       *return_value,
                                                   guint         n_param_values,
                                                   const GValue *param_values,
                                                   gpointer      invocation_hint,
                                                   gpointer      marshal_data);

G_END_DECLS

#endif /* __gs_marshal_MARSHAL_H__ */

