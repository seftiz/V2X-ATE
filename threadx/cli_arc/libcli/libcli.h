#ifndef __LIBCLI_H__
#define __LIBCLI_H__

// vim:sw=4 tw=120 et

#ifdef __cplusplus
extern "C" {
#endif

/**
   @file
   libcli API
*/

#include <stdio.h>
#include <stdarg.h>
#include <sys/time.h>

#define CLI_OK                  0
#define CLI_ERROR               -1
#define CLI_QUIT                -2
#define CLI_ERROR_ARG           -3

#define MAX_HISTORY             256

#define PRIVILEGE_UNPRIVILEGED  0
#define PRIVILEGE_PRIVILEGED    15
#define MODE_ANY                -1
#define MODE_EXEC               0
#define MODE_CONFIG             1

#define LIBCLI_HAS_ENABLE       1

#define PRINT_PLAIN             0
#define PRINT_FILTERED          0x01
#define PRINT_BUFFERED          0x02

#define CLI_MAX_LINE_LENGTH     4096
#define CLI_MAX_LINE_WORDS      128

enum cli_states {
    STATE_LOGIN,
    STATE_PASSWORD,
    STATE_NORMAL,
    STATE_ENABLE_PASSWORD,
    STATE_ENABLE,
    STATE_SPECIAL
};

enum cli_protocols {
	CLI_PROTOCOL_UART 		=	0x0,
	CLI_PROTOCOL_TELNET 	= 	0x1,
	CLI_PROTOCOL_IMQ
	
};


/**
   libcli command definition.
*/
struct cli_def {
    int completion_callback;
    struct cli_command *commands;
    int (*auth_callback)(const char *, const char *);
    int (*regular_callback)(struct cli_def *cli);
    int (*enable_callback)(const char *);
    char *banner;
    struct unp *users;
    char *enable_password;
    char *history[MAX_HISTORY];
    char showprompt;
    char *promptchar;
    char *hostname;
    char *modestring;
    int privilege;
    int mode;
    int state;
    struct cli_filter *filters;
    void (*print_callback)(struct cli_def *cli, const char *string);
    FILE *client;
    int client_fd;
    /* internal buffers */
    void *conn;
    void *service;
    char *commandname;  // temporary buffer for cli_command_name() to prevent leak
    char *buffer;
    unsigned buf_size;
    struct timeval timeout_tm;
    time_t idle_timeout;
    int (*idle_timeout_callback)(struct cli_def *);
    time_t last_action;
    int protocol;
    void *user_context;

    /* Temporary buffer for using fprintf-like calls */
    char _fprintf_buf[300];
    int _fprintf_len;

    struct {
       int (*prompt_cb)(struct cli_def *cli, int sockfd);
       int (*process_cb)(struct cli_def *cli, char *cmd);
    } special;
};

/**
   libcli command filter.
*/
struct cli_filter {
    int (*filter)(struct cli_def *cli, const char *string, void *data);
    void *data;
    struct cli_filter *next;
};

/**
   libcli command handle.
*/
struct cli_command {
    char *command;
    int (*callback)(struct cli_def *, const char *, char **, int);
    unsigned int unique_len;
    char *help;
    int privilege;
    int mode;
    struct cli_command *next;
    struct cli_command *children;
    struct cli_command *parent;
};

struct cli_def *cli_init(void);
int cli_done(struct cli_def *cli);
struct cli_command *cli_register_command(struct cli_def *cli, struct cli_command *parent, const char *command,
                                         int (*callback)(struct cli_def *, const char *, char **, int), int privilege,
                                         int mode, const char *help);
int cli_unregister_command(struct cli_def *cli, const char *command);
int cli_run_command(struct cli_def *cli, const char *command);
int cli_loop(struct cli_def *cli, int sockfd);
int cli_file(struct cli_def *cli, FILE *fh, int privilege, int mode);
void cli_set_auth_callback(struct cli_def *cli, int (*auth_callback)(const char *, const char *));
void cli_set_enable_callback(struct cli_def *cli, int (*enable_callback)(const char *));
void cli_allow_user(struct cli_def *cli, const char *username, const char *password);
void cli_allow_enable(struct cli_def *cli, const char *password);
void cli_deny_user(struct cli_def *cli, const char *username);
void cli_set_banner(struct cli_def *cli, const char *banner);
void cli_set_hostname(struct cli_def *cli, const char *hostname);
void cli_set_promptchar(struct cli_def *cli, const char *promptchar);
void cli_set_modestring(struct cli_def *cli, const char *modestring);
int cli_set_privilege(struct cli_def *cli, int privilege);
int cli_set_configmode(struct cli_def *cli, int mode, const char *config_desc);
void cli_reprompt(struct cli_def *cli);
void cli_regular(struct cli_def *cli, int (*callback)(struct cli_def *cli));
void cli_regular_interval(struct cli_def *cli, int seconds);
void cli_print(struct cli_def *cli, const char *format, ...) __attribute__((format (printf, 2, 3)));
void cli_bufprint(struct cli_def *cli, const char *format, ...) __attribute__((format (printf, 2, 3)));
void cli_vabufprint(struct cli_def *cli, const char *format, va_list ap);
void cli_error(struct cli_def *cli, const char *format, ...) __attribute__((format (printf, 2, 3)));
void cli_print_callback(struct cli_def *cli, void (*callback)(struct cli_def *, const char *));
void cli_free_history(struct cli_def *cli);
void cli_set_idle_timeout(struct cli_def *cli, unsigned int seconds);
void cli_set_idle_timeout_callback(struct cli_def *cli, unsigned int seconds, int (*callback)(struct cli_def *));

/**
 * Check if interface index is valid
 * @param [in] cli Print error in case if is not valid.
 * @param [in] if_index Interface index to check.
 * @return 1 if valid, 0 otherwise.
 */
int cli_check_valid_if_index(struct cli_def *cli, int if_index);

// Enable or disable telnet protocol negotiation.
// Note that this is enabled by default and must be changed before cli_loop() is run.
void cli_protocol(struct cli_def *cli, int protocol);

// Set/get user context
void cli_set_context(struct cli_def *cli, void *context);
void *cli_get_context(struct cli_def *cli);

int cli_port_send(struct cli_def *cli, int socket,const char* str, int len, int flags);

/** @} */

#ifdef __cplusplus
}
#endif

#endif
