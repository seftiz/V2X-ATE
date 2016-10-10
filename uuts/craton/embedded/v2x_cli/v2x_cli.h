

#ifndef __V2X_CLI_H__
#define __V2X_CLI_H__

#define CLITEST_PORT                8000
#define MODE_CONFIG_INT             10

#define USERNAME					"root"
#define PASSWORD					"root"

#ifdef __GNUC__
# define UNUSED(d) d __attribute__ ((unused))
#else
# define UNUSED(d) d
#endif

#define __USE_API_DEFAULTS__


#define GET_INT(_parameter_,_var_,_idx_,_user_msg_) {  \
    if ( (argv[i] != NULL) && (strcmp(argv[i], _parameter_) == 0) ) {           \
      int value = 0;                           \
      int par_idx = (_idx_+1);                          \
      if (!argv[par_idx] && !&argv[par_idx]) {          \
          cli_print(cli, _user_msg_);                   \
          return CLI_OK;                                \
      }                                                 \
      sscanf(argv[par_idx], "%d", &value);              \
      _var_ = value;                                   \
	  cli_print( cli, "DEBUG : Processed parameter %s, value %d" , _parameter_ , value );\
    }                                                   \
}

#define GET_STRING(_parameter_,_var_,_idx_,_user_msg_) {  \
    if ( (argv[i] != NULL) && (strcmp(argv[i], _parameter_) == 0) ) {           \
      int par_idx = (_idx_+1);                          \
      if (!argv[par_idx] && !&argv[par_idx]) {          \
          cli_print(cli, _user_msg_);                   \
          return CLI_OK;                                \
      }     											\
	  sscanf(argv[par_idx], "%s", (char*) &_var_);    	\
	  cli_print( cli, "DEBUG : Processed parameter %s, value %s" , _parameter_ , _var_ );\
    }                                                   \
}

#define CHECK_NUM_ARGS \
	if ( (argc % 2) != 0 ) { \
    cli_print(cli, "Error : number of argument is mismatch" ); \
    return CLI_ERROR_ARG; \
	}

#define IS_HELP_ARG(_err_usage_)\
  if ( (argv[0] != NULL) && (strcmp(argv[0], "?") == 0) ) {\
    cli_print(cli, "usage : %s" , _err_usage_ );\
    return CLI_OK;\
  }

#endif /* __V2X_CLI_H__ */


